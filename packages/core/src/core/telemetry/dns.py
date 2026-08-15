from dataclasses import dataclass, field
from typing import List, Optional

import httpx


@dataclass
class DnsInspectionResult:
    domain: str
    score: int
    spf_valid: bool
    spf_record: Optional[str]
    spf_status: str
    dmarc_valid: bool
    dmarc_record: Optional[str]
    dmarc_status: str
    dkim_valid: bool
    dkim_selectors_found: List[str]
    dkim_status: str
    mx_valid: bool
    mx_records: List[str]
    mx_status: str
    recommendations: List[str] = field(default_factory=list)


class DnsDeliverabilityInspector:
    """Async DNS over HTTPS (DoH) inspector for SPF, DMARC, DKIM, and MX health."""

    COMMON_DKIM_SELECTORS = [
        "google",
        "default",
        "k1",
        "selector1",
        "s1",
        "m1",
        "smtp",
        "mail",
    ]

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self._client = client

    @staticmethod
    def _clean_domain(domain: str) -> str:
        d = domain.strip().lower()
        if "@" in d:
            d = d.split("@", 1)[1]
        if d.startswith("http://"):
            d = d[7:]
        elif d.startswith("https://"):
            d = d[8:]
        return d.split("/")[0].split(":")[0].strip()

    async def _query_doh(self, name: str, rtype: str) -> List[str]:
        """Query Cloudflare / Google DoH API for DNS records."""
        url = f"https://dns.google/resolve?name={name}&type={rtype}"
        try:
            if self._client:
                res = await self._client.get(url, timeout=5.0)
            else:
                async with httpx.AsyncClient() as client:
                    res = await client.get(url, timeout=5.0)

            if res.status_code == 200:
                data = res.json()
                answers = data.get("Answer", [])
                records = []
                for ans in answers:
                    data_str = ans.get("data", "").strip('"').strip()
                    if data_str:
                        records.append(data_str)
                return records
        except Exception:
            pass
        return []

    async def inspect(self, domain: str) -> DnsInspectionResult:
        clean_d = self._clean_domain(domain)
        if not clean_d or "." not in clean_d:
            return DnsInspectionResult(
                domain=clean_d or domain,
                score=0,
                spf_valid=False,
                spf_record=None,
                spf_status="Invalid domain format",
                dmarc_valid=False,
                dmarc_record=None,
                dmarc_status="Invalid domain format",
                dkim_valid=False,
                dkim_selectors_found=[],
                dkim_status="Invalid domain format",
                mx_valid=False,
                mx_records=[],
                mx_status="Invalid domain format",
                recommendations=["Please provide a valid domain (e.g. acme.com or user@acme.com)"],
            )

        score = 0
        recommendations: List[str] = []

        # 1. Inspect SPF Record
        txt_records = await self._query_doh(clean_d, "TXT")
        spf_record = next((r for r in txt_records if r.startswith("v=spf1")), None)
        if spf_record:
            if "+all" in spf_record:
                spf_valid = False
                spf_status = "Dangerous (+all permits any host to spoof)"
                recommendations.append(
                    "Change '+all' to '~all' (SoftFail) or '-all' (HardFail) in your SPF record."
                )
                score += 5
            elif "-all" in spf_record or "~all" in spf_record:
                spf_valid = True
                spf_status = (
                    "Valid (Strict alignment)" if "-all" in spf_record else "Valid (SoftFail)"
                )
                score += 30
            else:
                spf_valid = True
                spf_status = "Configured (Neutral/Unspecified all)"
                score += 20
        else:
            spf_valid = False
            spf_status = "Missing SPF record"
            recommendations.append(
                f"Add a TXT record for '{clean_d}' with value: "
                "'v=spf1 include:_spf.google.com ~all'"
            )

        # 2. Inspect DMARC Record
        dmarc_txt = await self._query_doh(f"_dmarc.{clean_d}", "TXT")
        dmarc_record = next((r for r in dmarc_txt if r.startswith("v=DMARC1")), None)
        if dmarc_record:
            if "p=reject" in dmarc_record or "p=quarantine" in dmarc_record:
                dmarc_valid = True
                policy = "reject" if "p=reject" in dmarc_record else "quarantine"
                dmarc_status = f"Enforced ({policy})"
                score += 30
            else:
                dmarc_valid = True
                dmarc_status = "Monitoring mode (p=none)"
                recommendations.append(
                    "Strengthen DMARC policy from 'p=none' to 'p=quarantine' or 'p=reject'."
                )
                score += 20
        else:
            dmarc_valid = False
            dmarc_status = "Missing DMARC record"
            recommendations.append(
                f"Add a TXT record for '_dmarc.{clean_d}' with value: "
                "'v=DMARC1; p=quarantine; sp=quarantine;'"
            )

        # 3. Inspect DKIM Records (Probe common selectors)
        dkim_found: List[str] = []
        for sel in self.COMMON_DKIM_SELECTORS:
            dkim_res = await self._query_doh(f"{sel}._domainkey.{clean_d}", "TXT")
            if any("k=rsa" in r or "p=" in r or "v=DKIM1" in r for r in dkim_res):
                dkim_found.append(sel)

        if dkim_found:
            dkim_valid = True
            dkim_status = f"Active ({', '.join(dkim_found)})"
            score += 25
        else:
            dkim_valid = False
            dkim_status = "No common selector found"
            recommendations.append(
                "Ensure your email provider DKIM selector (e.g. google._domainkey) is published."
            )

        # 4. Inspect MX Records
        mx_records = await self._query_doh(clean_d, "MX")
        if mx_records:
            mx_valid = True
            server_word = "servers" if len(mx_records) > 1 else "server"
            mx_status = f"Active ({len(mx_records)} mail exchange {server_word})"
            score += 15
        else:
            mx_valid = False
            mx_status = "No MX records found"
            recommendations.append(f"Configure MX records on '{clean_d}' to receive reply emails.")

        score = min(100, score)

        return DnsInspectionResult(
            domain=clean_d,
            score=score,
            spf_valid=spf_valid,
            spf_record=spf_record,
            spf_status=spf_status,
            dmarc_valid=dmarc_valid,
            dmarc_record=dmarc_record,
            dmarc_status=dmarc_status,
            dkim_valid=dkim_valid,
            dkim_selectors_found=dkim_found,
            dkim_status=dkim_status,
            mx_valid=mx_valid,
            mx_records=mx_records,
            mx_status=mx_status,
            recommendations=recommendations,
        )
