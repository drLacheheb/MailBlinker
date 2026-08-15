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
