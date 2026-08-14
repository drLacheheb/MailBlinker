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
