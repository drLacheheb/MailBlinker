from datetime import datetime, timedelta, timezone

from core.telemetry import TelemetryInspector


def test_classify_bot_scanner_latency():
    inspector = TelemetryInspector()
    sent_at = datetime.now(timezone.utc)
    open_time = sent_at + timedelta(seconds=1.5)

    result = inspector.inspect(
        email_id=1,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
        accept_language=None,
        past_events=[],
        geo_data=(None, None, None, None),
    )
    assert not result.is_valid_open
    assert result.elapsed_seconds < 3.0


def test_classify_bot_scanner_crawler_ua():
    inspector = TelemetryInspector()
    sent_at = datetime.now(timezone.utc)
    open_time = sent_at + timedelta(minutes=5)

    result = inspector.inspect(
        email_id=1,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="127.0.0.1",
        user_agent="Mimecast Security Scanner",
        accept_language=None,
        past_events=[],
        geo_data=(None, None, None, None),
    )
    assert not result.is_valid_open


def test_classify_crawlerdetect_match():
    inspector = TelemetryInspector()
    sent_at = datetime.now(timezone.utc)
    open_time = sent_at + timedelta(minutes=5)

    result = inspector.inspect(
        email_id=1,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="127.0.0.1",
        user_agent="curl/7.68.0",
        accept_language=None,
        past_events=[],
        geo_data=(None, None, None, None),
    )
    assert not result.is_valid_open


def test_classify_proxy_google_image_proxy():
    inspector = TelemetryInspector()
    sent_at = datetime.now(timezone.utc)
    open_time = sent_at + timedelta(minutes=10)

    result = inspector.inspect(
        email_id=1,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="127.0.0.1",
        user_agent="GoogleImageProxy",
        accept_language=None,
        past_events=[],
        geo_data=(None, None, None, None),
    )
    assert result.is_valid_open
    assert "Google Image Proxy" in result.device_summary


def test_classify_human_open():
    inspector = TelemetryInspector()
    sent_at = datetime.now(timezone.utc)
    open_time = sent_at + timedelta(hours=2, minutes=15)

    result = inspector.inspect(
        email_id=1,
        sent_at=sent_at,
        open_time=open_time,
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        accept_language="fr-FR,fr;q=0.9",
        past_events=[],
        geo_data=("France", "Île-de-France", "Paris", "Orange"),
    )
    assert result.is_valid_open
    assert "iPhone" in result.device_summary
    assert result.event is not None
    assert result.event.city == "Paris"
    assert result.event.language is not None and "French" in result.event.language
