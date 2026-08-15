from datetime import datetime, timezone

import pytest
from core.domain.entities import OpenEventEntity
from core.infrastructure import HttpGeoIpResolver, is_private_or_local_ip
from core.telemetry import (
    detect_forwarding_clues,
    format_elapsed_time,
    parse_accept_language,
)


def test_private_ip_detection():
    assert is_private_or_local_ip("127.0.0.1") is True
    assert is_private_or_local_ip("192.168.1.1") is True
    assert is_private_or_local_ip("10.0.0.1") is True
    assert is_private_or_local_ip("8.8.8.8") is False


@pytest.mark.asyncio
async def test_resolve_geoip_private():
    resolver = HttpGeoIpResolver()
    country, region, city, isp = await resolver.resolve("127.0.0.1")
    assert country is None
    assert city is None


def test_parse_accept_language():
    res_fr = parse_accept_language("fr-FR,fr;q=0.9,en-US;q=0.8")
    assert res_fr is not None
    assert "French" in res_fr and "France" in res_fr

    res_en = parse_accept_language("en-US,en;q=0.9")
    assert res_en is not None
    assert "English" in res_en and "United States" in res_en

    assert parse_accept_language(None) is None


def test_format_elapsed_time():
    assert format_elapsed_time(45.0) == "45s"
    assert format_elapsed_time(125.0) == "2m 5s"
    assert format_elapsed_time(3700.0) == "1h 1m"


def test_detect_forwarding_clues():
    now = datetime.now(timezone.utc)
    ev1 = OpenEventEntity(
        id=1,
        email_id=1,
        timestamp=now,
        ip_address="82.120.1.1",
        city="Paris",
        country="France",
        device_model="iPhone",
    )

    clue = detect_forwarding_clues([ev1], "New York, United States", "198.51.100.1", "Windows PC")
    assert clue is not None
    assert "New location" in clue or "New device" in clue


def test_apple_mail_privacy_protection_detection():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    now = datetime.now(timezone.utc)
    sent_at = datetime.fromtimestamp(now.timestamp() - 60, tz=timezone.utc)

    # 1. Test Apple 17.x.x.x subnet detection
    res1 = inspector.inspect(
        email_id=1,
        sent_at=sent_at,
        open_time=now,
        ip_address="17.248.1.5",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        accept_language="en-US",
        past_events=[],
        geo_data=("United States", "California", "Cupertino", "Apple Inc."),
    )
    assert res1.is_valid_open is True
    assert res1.device_summary == "Apple Mail (Privacy Proxy)"
    assert res1.event is not None
    assert res1.event.browser_name == "Apple Mail (Privacy Proxy)"

    # 2. Test Apple Mail UA token detection
    res2 = inspector.inspect(
        email_id=2,
        sent_at=sent_at,
        open_time=now,
        ip_address="198.51.100.2",
        user_agent="Mozilla/5.0 Apple-Mail-Privacy-Protection/1.0",
        accept_language="en-US",
        past_events=[],
        geo_data=("United States", "Texas", "Dallas", "Cloudflare"),
    )
    assert res2.is_valid_open is True
    assert "Apple Mail" in res2.device_summary


def test_spoofed_mobile_ua_detection():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    now = datetime.now(timezone.utc)
    sent_at = datetime.fromtimestamp(now.timestamp() - 60, tz=timezone.utc)

    # Spoofed iPhone UA coming from AWS datacenter without language header
    res = inspector.inspect(
        email_id=3,
        sent_at=sent_at,
        open_time=now,
        ip_address="54.210.1.1",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        accept_language=None,
        past_events=[],
        geo_data=("United States", "Virginia", "Ashburn", "Amazon.com, Inc. (AWS)"),
    )
    assert res.is_valid_open is False
    assert res.device_summary == "Automated Scraper (Spoofed UA)"


@pytest.mark.asyncio
async def test_dns_deliverability_inspector():
    from core import DnsDeliverabilityInspector

    inspector = DnsDeliverabilityInspector()
    # Test invalid domain
    res_invalid = await inspector.inspect("not-a-domain")
    assert res_invalid.score == 0
    assert res_invalid.spf_valid is False

    # Test real domain DoH lookup
    res_gmail = await inspector.inspect("gmail.com")
    assert res_gmail.domain == "gmail.com"
    assert res_gmail.score >= 50
    assert res_gmail.mx_valid is True
    assert hasattr(res_gmail, "dkim_valid")
    assert hasattr(res_gmail, "dkim_status")
    assert hasattr(res_gmail, "ptr_valid")
    assert hasattr(res_gmail, "ptr_status")
    assert hasattr(res_gmail, "bimi_valid")
    assert hasattr(res_gmail, "bimi_status")
    assert hasattr(res_gmail, "mta_sts_valid")
    assert hasattr(res_gmail, "mta_sts_status")
    assert hasattr(res_gmail, "tls_rpt_valid")
    assert hasattr(res_gmail, "tls_rpt_status")
    assert hasattr(res_gmail, "mx_ipv6_valid")
    assert hasattr(res_gmail, "dane_valid")
    assert hasattr(res_gmail, "dane_status")
    assert hasattr(res_gmail, "arc_valid")
    assert hasattr(res_gmail, "arc_status")
    assert hasattr(res_gmail, "dnsbl_listed")
    assert hasattr(res_gmail, "dnsbl_status")
    assert hasattr(res_gmail, "crypto_discovery_valid")
    assert hasattr(res_gmail, "crypto_discovery_status")
    assert hasattr(res_gmail, "spf_lookup_count")
    assert hasattr(res_gmail, "null_mx_declared")
    assert hasattr(res_gmail, "caa_valid")
    assert hasattr(res_gmail, "dmarc_forensic_valid")
    assert hasattr(res_gmail, "dnssec_valid")
    assert hasattr(res_gmail, "dane_smtp_valid")
    assert hasattr(res_gmail, "fcrdns_aligned")
    assert hasattr(res_gmail, "ns_valid")
    assert hasattr(res_gmail, "ns_records")
    assert hasattr(res_gmail, "dkim_ed25519_valid")
    assert hasattr(res_gmail, "openpgpkey_valid")
    assert hasattr(res_gmail, "dmarc_tree_walk_valid")
    assert hasattr(res_gmail, "dns_any_hardened")


def test_headless_probe_telemetry():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    sent_at = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    open_time = datetime(2026, 8, 15, 12, 5, 0, tzinfo=timezone.utc)

    res = inspector.inspect(
        email_id=9,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="198.51.100.5",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) HeadlessChrome/125.0.0.0",
        accept_language=None,
        past_events=[],
        geo_data=("United States", "California", "San Jose", "DataCamp"),
    )
    assert res.is_valid_open is False
    assert "Headless" in res.device_summary


def test_off_hours_telemetry_heuristics():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    # 03:00 AM UTC (Off-hours probe)
    off_hours_time = datetime(2026, 8, 15, 3, 30, 0, tzinfo=timezone.utc)
    sent_at = datetime(2026, 8, 15, 3, 0, 0, tzinfo=timezone.utc)

    # 1. Off-hours datacenter probe without language header
    dc_probe = inspector.inspect(
        email_id=5,
        sent_at=sent_at,
        open_time=off_hours_time,
        ip_address="142.250.190.46",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        accept_language=None,
        past_events=[],
        geo_data=("United States", "California", "Mountain View", "Google Cloud"),
    )
    assert dc_probe.is_valid_open is False
    assert "Off-Hours" in dc_probe.device_summary

    # 2. Human open during off-hours with full language header
    human_open = inspector.inspect(
        email_id=6,
        sent_at=sent_at,
        open_time=off_hours_time,
        ip_address="198.51.100.1",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
        accept_language="en-US,en;q=0.9",
        past_events=[],
        geo_data=("United Kingdom", "England", "London", "Virgin Media"),
    )
    assert human_open.is_valid_open is True
    assert human_open.forwarding_note is not None
    assert "off-hours" in human_open.forwarding_note.lower()


def test_parse_dmarc_rua_xml():
    from core import parse_dmarc_rua_xml

    sample_xml = """<?xml version="1.0" encoding="UTF-8" ?>
    <feedback>
      <report_metadata>
        <org_name>google.com</org_name>
        <report_id>123456789</report_id>
      </report_metadata>
      <policy_published>
        <domain>example.com</domain>
      </policy_published>
      <record>
        <row>
          <source_ip>209.85.220.41</source_ip>
          <count>15</count>
          <policy_evaluated>
            <disposition>none</disposition>
            <dkim>pass</dkim>
            <spf>pass</spf>
          </policy_evaluated>
        </row>
        <identifiers>
          <header_from>example.com</header_from>
        </identifiers>
      </record>
      <record>
        <row>
          <source_ip>198.51.100.99</source_ip>
          <count>2</count>
          <policy_evaluated>
            <disposition>quarantine</disposition>
            <dkim>fail</dkim>
            <spf>fail</spf>
          </policy_evaluated>
        </row>
      </record>
    </feedback>
    """
    summary = parse_dmarc_rua_xml(sample_xml)
    assert summary.org_name == "google.com"
    assert summary.domain == "example.com"
    assert summary.total_messages == 17
    assert summary.passed_count == 15
    assert summary.failed_count == 2
    assert len(summary.records) == 2
    assert summary.records[0].dkim_result == "pass"
    assert summary.records[1].source_ip == "198.51.100.99"


def test_prefetch_and_client_hints_telemetry():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    sent_at = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    open_time = datetime(2026, 8, 15, 12, 5, 0, tzinfo=timezone.utc)

    # 1. Speculative Prefetch request
    res_prefetch = inspector.inspect(
        email_id=12,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="198.51.100.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        accept_language="en-US,en;q=0.9",
        past_events=[],
        geo_data=("United States", "New York", "New York", "Verizon"),
        purpose="prefetch",
    )
    assert res_prefetch.is_valid_open is False
    assert "Prefetch" in res_prefetch.device_summary

    # 2. Forged Client-Hints (UA claims Windows, hints claim Linux)
    res_forged = inspector.inspect(
        email_id=13,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="198.51.100.2",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        accept_language="en-US,en;q=0.9",
        past_events=[],
        geo_data=("United States", "New York", "New York", "Verizon"),
        client_hints={"sec-ch-ua-platform": '"Linux"'},
    )
    assert res_forged.is_valid_open is False
    assert "Forged Client Hints" in res_forged.device_summary


def test_tls_middlebox_downgrade_telemetry():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    sent_at = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    open_time = datetime(2026, 8, 15, 12, 5, 0, tzinfo=timezone.utc)

    # Legacy TLS 1.0 middlebox proxy
    res = inspector.inspect(
        email_id=14,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="198.51.100.8",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        accept_language="en-US,en;q=0.9",
        past_events=[],
        geo_data=("United States", "Virginia", "Reston", "Corporate Proxy"),
        tls_version="TLS 1.0",
    )
    assert res.is_valid_open is False
    assert "Legacy TLS Downgrade" in res.device_summary


def test_haversine_distance_telemetry():
    from core.telemetry.inspector import calculate_haversine_distance

    # Paris (48.8566, 2.3522) to London (51.5074, -0.1278) -> ~343 km
    dist_km = calculate_haversine_distance(48.8566, 2.3522, 51.5074, -0.1278)
    assert 340.0 <= dist_km <= 350.0

    # Same location -> 0.0 km
    dist_zero = calculate_haversine_distance(40.7128, -74.0060, 40.7128, -74.0060)
    assert dist_zero == 0.0


def test_datacenter_asn_telemetry():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    sent_at = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    open_time = datetime(2026, 8, 15, 12, 5, 0, tzinfo=timezone.utc)

    res = inspector.inspect(
        email_id=15,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="3.80.12.34",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        accept_language="en-US,en;q=0.9",
        past_events=[],
        geo_data=("United States", "Virginia", "Ashburn", "Amazon.com AWS"),
    )
    assert res.is_valid_open is True
    assert "[Datacenter ASN]" in res.device_summary


def test_software_renderer_telemetry():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    sent_at = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    open_time = datetime(2026, 8, 15, 12, 5, 0, tzinfo=timezone.utc)

    res = inspector.inspect(
        email_id=16,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="198.51.100.12",
        user_agent="Mozilla/5.0 (X11; Linux x86_64) SwiftShader/4.0 Chrome/120.0.0.0",
        accept_language="en-US,en;q=0.9",
        past_events=[],
        geo_data=("United States", "California", "San Jose", "Residential Comcast"),
    )
    assert res.is_valid_open is True
    assert "[Software Renderer Sandbox]" in res.device_summary


def test_high_velocity_forward_telemetry():
    from core.domain.entities import OpenEventEntity
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    sent_at = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 8, 15, 12, 1, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 15, 12, 2, 0, tzinfo=timezone.utc)
    open_time = datetime(2026, 8, 15, 12, 3, 0, tzinfo=timezone.utc)

    past = [
        OpenEventEntity(
            id=1,
            email_id=17,
            timestamp=t1,
            ip_address="198.51.100.1",
            country="US",
            region="NY",
            city="New York",
            isp="Verizon",
            device_model="Desktop",
            os_name="Windows 11",
            browser_name="Chrome 120",
            language="en-US",
            user_agent="UA1",
            elapsed_seconds=60,
        ),
        OpenEventEntity(
            id=2,
            email_id=17,
            timestamp=t2,
            ip_address="198.51.100.2",
            country="US",
            region="CA",
            city="San Francisco",
            isp="Comcast",
            device_model="Desktop",
            os_name="macOS 14",
            browser_name="Safari 17",
            language="en-US",
            user_agent="UA2",
            elapsed_seconds=120,
        ),
    ]

    res = inspector.inspect(
        email_id=17,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="198.51.100.3",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        accept_language="en-US,en;q=0.9",
        past_events=past,
        geo_data=("United States", "TX", "Austin", "AT&T"),
    )
    assert res.is_valid_open is True
    assert res.forwarding_note is not None
    assert "High-Velocity Team Forward" in res.forwarding_note


def test_microvm_sandbox_telemetry():
    from core.telemetry.inspector import TelemetryInspector

    inspector = TelemetryInspector()
    sent_at = datetime(2026, 8, 15, 12, 0, 0, tzinfo=timezone.utc)
    open_time = datetime(2026, 8, 15, 12, 5, 0, tzinfo=timezone.utc)

    res = inspector.inspect(
        email_id=18,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="198.51.100.22",
        user_agent="Mozilla/5.0 (X11; Linux x86_64) Firecracker/1.0 Chrome/120.0.0.0",
        accept_language="en-US,en;q=0.9",
        past_events=[],
        geo_data=("United States", "California", "San Jose", "Residential Comcast"),
    )
    assert res.is_valid_open is True
    assert "[Virtual MicroVM Sandbox]" in res.device_summary
