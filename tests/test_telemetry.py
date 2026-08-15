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
