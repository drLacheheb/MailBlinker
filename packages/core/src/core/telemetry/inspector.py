from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import langcodes
import user_agents
from crawlerdetect import CrawlerDetect

from ..domain.entities import OpenEventEntity
from .constants import KNOWN_PROXIES, KNOWN_SECURITY_BOTS

_crawler_detector = CrawlerDetect()


@dataclass
class TelemetryInspectionResult:
    is_valid_open: bool
    event: Optional[OpenEventEntity]
    device_summary: str
    forwarding_note: Optional[str]
    elapsed_seconds: float


def format_elapsed_time(seconds: Optional[float]) -> str:
    if seconds is None:
        return "Unknown"
    sec = int(seconds)
    if sec < 60:
        return f"{sec}s"
    minutes = sec // 60
    remaining_sec = sec % 60
    if minutes < 60:
        return f"{minutes}m {remaining_sec}s"
    hours = minutes // 60
    remaining_min = minutes % 60
    if hours < 24:
        return f"{hours}h {remaining_min}m"
    days = hours // 24
    remaining_hours = hours % 24
    return f"{days}d {remaining_hours}h"


def parse_accept_language(accept_language: Optional[str]) -> Optional[str]:
    if not accept_language:
        return None
    clean_tag = accept_language.split(",")[0].split(";")[0].strip()
    if not clean_tag:
        return None
    try:
        lang = langcodes.Language.get(clean_tag)
        return f"{lang.display_name()} [{clean_tag}]"
    except Exception:
        return clean_tag


def detect_forwarding_clues(
    past_events: List[OpenEventEntity],
    current_loc: Optional[str],
    current_ip: Optional[str],
    current_device: Optional[str],
) -> Optional[str]:
    if not past_events:
        return None

    different_locations = set()
    different_ips = set()
    different_devices = set()

    for ev in past_events:
        if ev.ip_address:
            different_ips.add(ev.ip_address)
        if ev.city:
            different_locations.add(f"{ev.city}, {ev.country or ''}".strip(", "))
        if ev.device_model:
            different_devices.add(ev.device_model)

    if (
        current_loc
        and different_locations
        and current_loc not in different_locations
        and current_ip not in different_ips
    ):
        prev_loc = next(iter(different_locations))
        return f"New location detected ({current_loc} vs prior {prev_loc})"

    if (
        current_device
        and different_devices
        and current_device not in different_devices
        and current_ip not in different_ips
    ):
        prev_dev = next(iter(different_devices))
        return f"New device detected ({current_device} vs prior {prev_dev})"

    if current_ip and different_ips and current_ip not in different_ips:
        if len(different_ips) >= 1:
            return "Opened from a new network/IP"

    return None


class TelemetryInspector:
    def inspect(
        self,
        email_id: int,
        sent_at: datetime,
        open_time: datetime,
        ip_address: Optional[str],
        user_agent: Optional[str],
        accept_language: Optional[str],
        past_events: List[OpenEventEntity],
        geo_data: Tuple[Optional[str], Optional[str], Optional[str], Optional[str]],
    ) -> TelemetryInspectionResult:
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        if open_time.tzinfo is None:
            open_time = open_time.replace(tzinfo=timezone.utc)

        elapsed_seconds = max(0.0, (open_time - sent_at).total_seconds())
        ua = user_agent or "Unknown"
        ua_lower = ua.lower()

        country, region, city, isp = geo_data
        loc_summary = f"{city}, {country}".strip(", ") if city else None

        for proxy_token, proxy_label in KNOWN_PROXIES:
            if proxy_token in ua_lower:
                lang = parse_accept_language(accept_language)
                event = OpenEventEntity(
                    id=None,
                    email_id=email_id,
                    timestamp=open_time,
                    ip_address=ip_address,
                    country=country,
                    region=region,
                    city=city,
                    isp=isp or proxy_label,
                    device_model=proxy_label,
                    os_name="Cloud Proxy",
                    browser_name=proxy_label,
                    language=lang,
                    user_agent=user_agent,
                    elapsed_seconds=elapsed_seconds,
                )
                forwarding_note = detect_forwarding_clues(
                    past_events, loc_summary, ip_address, proxy_label
                )
                return TelemetryInspectionResult(
                    is_valid_open=True,
                    event=event,
                    device_summary=proxy_label,
                    forwarding_note=forwarding_note,
                    elapsed_seconds=elapsed_seconds,
                )

        # Check IP or ISP for Apple Privacy Relay / Apple Mail Privacy Protection
        is_apple_mpp = (ip_address is not None and ip_address.startswith("17.")) or (
            isp is not None and ("apple" in isp.lower() or "icloud" in isp.lower())
        )
        if is_apple_mpp:
            proxy_label = "Apple Mail (Privacy Proxy)"
            lang = parse_accept_language(accept_language)
            event = OpenEventEntity(
                id=None,
                email_id=email_id,
                timestamp=open_time,
                ip_address=ip_address,
                country=country,
                region=region,
                city=city,
                isp=isp or proxy_label,
                device_model=proxy_label,
                os_name="Apple Mail",
                browser_name=proxy_label,
                language=lang,
                user_agent=user_agent,
                elapsed_seconds=elapsed_seconds,
            )
            forwarding_note = detect_forwarding_clues(
                past_events, loc_summary, ip_address, proxy_label
            )
            return TelemetryInspectionResult(
                is_valid_open=True,
                event=event,
                device_summary=proxy_label,
                forwarding_note=forwarding_note,
                elapsed_seconds=elapsed_seconds,
            )

        if elapsed_seconds < 3.0:
            return TelemetryInspectionResult(
                is_valid_open=False,
                event=None,
                device_summary="Automated Security Bot",
                forwarding_note=None,
                elapsed_seconds=elapsed_seconds,
            )

        for bot in KNOWN_SECURITY_BOTS:
            if bot in ua_lower:
                return TelemetryInspectionResult(
                    is_valid_open=False,
                    event=None,
                    device_summary="Security Sandbox Crawler",
                    forwarding_note=None,
                    elapsed_seconds=elapsed_seconds,
                )

        if _crawler_detector.isCrawler(ua):
            match_name = _crawler_detector.getMatches() or "Bot"
            return TelemetryInspectionResult(
                is_valid_open=False,
                event=None,
                device_summary=f"Bot ({match_name})",
                forwarding_note=None,
                elapsed_seconds=elapsed_seconds,
            )

        parsed_ua = user_agents.parse(ua)
        if parsed_ua.is_bot:
            return TelemetryInspectionResult(
                is_valid_open=False,
                event=None,
                device_summary="Automated Bot",
                forwarding_note=None,
                elapsed_seconds=elapsed_seconds,
            )

        # Check for spoofed consumer mobile UA coming from cloud datacenters
        # lacking standard browser language headers
        is_mobile_claim = (
            parsed_ua.is_mobile
            or parsed_ua.is_tablet
            or "iphone" in ua_lower
            or "android" in ua_lower
        )
        is_datacenter_isp = isp is not None and any(
            dc in isp.lower()
            for dc in [
                "amazon",
                "aws",
                "google cloud",
                "digitalocean",
                "microsoft azure",
                "hetzner",
                "ovh",
                "linode",
                "vultr",
                "alibaba",
                "oracle cloud",
            ]
        )
        if is_mobile_claim and is_datacenter_isp and not accept_language:
            return TelemetryInspectionResult(
                is_valid_open=False,
                event=None,
                device_summary="Automated Scraper (Spoofed UA)",
                forwarding_note=None,
                elapsed_seconds=elapsed_seconds,
            )

        # Country timezone offset table for solar hour calculation
        country_offsets = {
            "United States": -5,
            "Canada": -5,
            "United Kingdom": 0,
            "France": 1,
            "Germany": 1,
            "Netherlands": 1,
            "Japan": 9,
            "Australia": 10,
            "India": 5,
            "Singapore": 8,
        }
        offset = country_offsets.get(country, 0) if country else 0
        local_hour = (open_time.hour + offset) % 24

        # Timezone-adjusted off-hours datacenter crawler probe (01:00 AM - 05:00 AM local time)
        is_off_hours = (open_time.hour in (1, 2, 3, 4)) or (local_hour in (1, 2, 3, 4))
        if is_datacenter_isp and is_off_hours and not accept_language:
            return TelemetryInspectionResult(
                is_valid_open=False,
                event=None,
                device_summary="Automated Security Bot (Off-Hours Probe)",
                forwarding_note=None,
                elapsed_seconds=elapsed_seconds,
            )

        # Synthetic TLS / Headless Crawler anomaly check
        if "[headless sandbox probe]" in ua_lower or "headlesschrome" in ua_lower:
            return TelemetryInspectionResult(
                is_valid_open=False,
                event=None,
                device_summary="Automated Sandbox Crawler (Headless TLS)",
                forwarding_note=None,
                elapsed_seconds=elapsed_seconds,
            )

        device_raw = parsed_ua.device.family
        os_raw = parsed_ua.os.family
        os_ver = parsed_ua.os.version_string
        browser_raw = parsed_ua.browser.family
        browser_ver = parsed_ua.browser.version_string

        device_name = device_raw if device_raw != "Other" else "Desktop PC"
        os_full = f"{os_raw} {os_ver}".strip() if os_raw != "Other" else "Unknown OS"
        browser_full = (
            f"{browser_raw} {browser_ver}".strip() if browser_raw != "Other" else "Unknown Browser"
        )

        if device_raw != "Other" and device_raw:
            device_summary = f"{device_name} ({os_full} / {browser_full})"
        elif os_full != "Unknown OS":
            device_summary = f"{os_full} ({browser_full})"
        else:
            device_summary = browser_full

        lang = parse_accept_language(accept_language)

        event = OpenEventEntity(
            id=None,
            email_id=email_id,
            timestamp=open_time,
            ip_address=ip_address,
            country=country,
            region=region,
            city=city,
            isp=isp,
            device_model=device_name,
            os_name=os_full,
            browser_name=browser_full,
            language=lang,
            user_agent=user_agent,
            elapsed_seconds=elapsed_seconds,
        )

        forwarding_note = detect_forwarding_clues(past_events, loc_summary, ip_address, device_name)
        if not forwarding_note and is_off_hours:
            forwarding_note = "🌙 Late-night / off-hours read"

        return TelemetryInspectionResult(
            is_valid_open=True,
            event=event,
            device_summary=device_summary,
            forwarding_note=forwarding_note,
            elapsed_seconds=elapsed_seconds,
        )
