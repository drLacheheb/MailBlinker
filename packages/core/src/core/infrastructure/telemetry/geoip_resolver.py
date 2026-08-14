import ipaddress
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import httpx

_GEO_CACHE: Dict[str, "GeoLocationData"] = {}


@dataclass
class GeoLocationData:
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None


def is_private_or_local_ip(ip: str) -> bool:
    if not ip or ip in ("Unknown", "localhost"):
        return True
    try:
        parsed = ipaddress.ip_address(ip)
        return parsed.is_private or parsed.is_loopback or parsed.is_reserved
    except ValueError:
        return True


class HttpGeoIpResolver:
    def __init__(self, timeout: float = 2.5):
        self._timeout = timeout

    async def resolve(
        self, ip: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        if not ip or is_private_or_local_ip(ip):
            return None, None, None, None

        if ip in _GEO_CACHE:
            cached = _GEO_CACHE[ip]
            return cached.country, cached.region, cached.city, cached.isp

        url = f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status") == "success":
                        result = GeoLocationData(
                            country=data.get("country"),
                            region=data.get("regionName"),
                            city=data.get("city"),
                            isp=data.get("isp") or data.get("org"),
                        )
                        _GEO_CACHE[ip] = result
                        return result.country, result.region, result.city, result.isp
        except Exception:
            pass

        fallback = GeoLocationData()
        _GEO_CACHE[ip] = fallback
        return None, None, None, None
