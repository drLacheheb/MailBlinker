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
    spf_lookup_count: int
    dmarc_valid: bool
    dmarc_record: Optional[str]
    dmarc_status: str
    dkim_valid: bool
    dkim_selectors_found: List[str]
    dkim_status: str
    mx_valid: bool
    mx_records: List[str]
    mx_status: str
    mx_ipv6_valid: bool
    null_mx_declared: bool
    ptr_valid: bool
    ptr_record: Optional[str]
    ptr_status: str
    bimi_valid: bool
    bimi_record: Optional[str]
    bimi_status: str
    mta_sts_valid: bool
    mta_sts_status: str
    tls_rpt_valid: bool
    tls_rpt_status: str
    dane_valid: bool
    dane_record: Optional[str]
    dane_status: str
    arc_valid: bool
    arc_status: str
    dnsbl_listed: bool
    dnsbl_listings: List[str]
    dnsbl_status: str
    crypto_discovery_valid: bool
    crypto_discovery_status: str
    recommendations: List[str] = field(default_factory=list)


class DnsDeliverabilityInspector:
    """Async DNS over HTTPS (DoH) inspector with Multi-Provider Failover (Google, Cloudflare, Quad9)
    for SPF, DMARC, DKIM, MX, PTR, BIMI, MTA-STS, TLS-RPT, DANE, ARC, DNSBL,
    and S/MIME & OpenPGP health.
    """

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

    COMMON_ARC_SELECTORS = [
        "arc",
        "arc1",
        "google",
        "default",
        "s1",
    ]

    DNSBL_ZONES = [
        "zen.spamhaus.org",
        "b.barracudacentral.org",
        "bl.spamcop.net",
    ]

    DOH_PROVIDERS = [
        {"url": "https://dns.google/resolve", "headers": {}},
        {
            "url": "https://cloudflare-dns.com/dns-query",
            "headers": {"Accept": "application/dns-json"},
        },
        {
            "url": "https://dns.quad9.net:5053/dns-query",
            "headers": {"Accept": "application/dns-json"},
        },
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
        """Query Multi-Provider DoH pool (Google, Cloudflare, Quad9) with automatic failover."""
        for provider in self.DOH_PROVIDERS:
            endpoint = f"{provider['url']}?name={name}&type={rtype}"
            headers = provider["headers"]
            try:
                if self._client:
                    res = await self._client.get(endpoint, headers=headers, timeout=4.0)
                else:
                    async with httpx.AsyncClient() as client:
                        res = await client.get(endpoint, headers=headers, timeout=4.0)

                if res.status_code == 200:
                    data = res.json()
                    answers = data.get("Answer", [])
                    records = []
                    for ans in answers:
                        data_str = ans.get("data", "").strip('"').strip()
                        if data_str:
                            records.append(data_str)
                    if records:
                        return records
            except Exception:
                continue
        return []

    async def _count_spf_lookups(self, domain: str, visited: Optional[set[str]] = None) -> int:
        if visited is None:
            visited = set()
        clean = domain.strip().lower()
        if clean in visited or len(visited) > 15:
            return 0
        visited.add(clean)

        txts = await self._query_doh(clean, "TXT")
        spf = next((r for r in txts if r.startswith("v=spf1")), None)
        if not spf:
            return 0

        tokens = spf.split()
        count = 0
        for tok in tokens[1:]:
            tok_l = tok.lower()
            if tok_l.startswith("include:"):
                count += 1
                target = tok.split("include:", 1)[1]
                count += await self._count_spf_lookups(target, visited)
            elif tok_l.startswith("redirect="):
                count += 1
                target = tok.split("redirect=", 1)[1]
                count += await self._count_spf_lookups(target, visited)
            elif tok_l in ("a", "+a", "-a", "~a", "?a") or tok_l.startswith(
                ("a:", "+a:", "-a:", "~a:")
            ):
                count += 1
            elif tok_l in ("mx", "+mx", "-mx", "~mx", "?mx") or tok_l.startswith(
                ("mx:", "+mx:", "-mx:", "~mx:")
            ):
                count += 1
            elif tok_l in ("ptr", "+ptr", "-ptr", "~ptr") or tok_l.startswith("ptr:"):
                count += 1
            elif tok_l.startswith("exists:"):
                count += 1
        return count

    async def inspect(self, domain: str) -> DnsInspectionResult:
        clean_d = self._clean_domain(domain)
        if not clean_d or "." not in clean_d:
            return DnsInspectionResult(
                domain=clean_d or domain,
                score=0,
                spf_valid=False,
                spf_record=None,
                spf_status="Invalid domain format",
                spf_lookup_count=0,
                dmarc_valid=False,
                dmarc_record=None,
                dmarc_status="Invalid domain format",
                dkim_valid=False,
                dkim_selectors_found=[],
                dkim_status="Invalid domain format",
                mx_valid=False,
                mx_records=[],
                mx_status="Invalid domain format",
                mx_ipv6_valid=False,
                null_mx_declared=False,
                ptr_valid=False,
                ptr_record=None,
                ptr_status="Invalid domain format",
                bimi_valid=False,
                bimi_record=None,
                bimi_status="Invalid domain format",
                mta_sts_valid=False,
                mta_sts_status="Invalid domain format",
                tls_rpt_valid=False,
                tls_rpt_status="Invalid domain format",
                dane_valid=False,
                dane_record=None,
                dane_status="Invalid domain format",
                arc_valid=False,
                arc_status="Invalid domain format",
                dnsbl_listed=False,
                dnsbl_listings=[],
                dnsbl_status="Invalid domain format",
                crypto_discovery_valid=False,
                crypto_discovery_status="Invalid domain format",
                recommendations=["Please provide a valid domain (e.g. acme.com or user@acme.com)"],
            )

        score = 0
        recommendations: List[str] = []

        # 1. Inspect SPF Record
        txt_records = await self._query_doh(clean_d, "TXT")
        spf_record = next((r for r in txt_records if r.startswith("v=spf1")), None)
        spf_lookup_count = 0
        if spf_record:
            spf_lookup_count = await self._count_spf_lookups(clean_d)
            if spf_lookup_count > 10:
                spf_valid = False
                spf_status = f"PermError (Exceeds RFC 7208 10-lookup limit: {spf_lookup_count}/10)"
                recommendations.append(
                    f"Flatten your SPF record! You have {spf_lookup_count} DNS lookups (Max: 10)."
                )
                score = max(0, score - 20)
            elif "+all" in spf_record:
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
                score += 25
            else:
                spf_valid = True
                spf_status = "Configured (Neutral/Unspecified all)"
                score += 15
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
                score += 25
            else:
                dmarc_valid = True
                dmarc_status = "Monitoring mode (p=none)"
                recommendations.append(
                    "Strengthen DMARC policy from 'p=none' to 'p=quarantine' or 'p=reject'."
                )
                score += 15
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

        # 4. Inspect MX Records & IPv6 Dual-Stack Reachability
        mx_records = await self._query_doh(clean_d, "MX")
        mx_ipv6_valid = False
        null_mx_declared = False
        if mx_records:
            if any(
                r.strip() in ("0 .", "0 . .", "0") or r.strip().endswith(" 0 .") for r in mx_records
            ):
                null_mx_declared = True
                mx_valid = True
                mx_status = "RFC 7505 Null MX (Outbound-only subdomain, no inbound mail)"
                score += 10
            else:
                mx_valid = True
                server_word = "servers" if len(mx_records) > 1 else "server"
                mx_status = f"Active ({len(mx_records)} mail exchange {server_word})"
                score += 10

                first_mx_host = mx_records[0].split()[-1].rstrip(".")
                aaaa_records = await self._query_doh(first_mx_host, "AAAA")
                if aaaa_records:
                    mx_ipv6_valid = True
        else:
            mx_valid = False
            mx_status = "No MX records found"
            recommendations.append(f"Configure MX records on '{clean_d}' to receive reply emails.")

        # 5. Inspect A & Reverse DNS (PTR / FCrDNS)
        a_records = await self._query_doh(clean_d, "A")
        ptr_valid = False
        ptr_record = None
        ptr_status = "No A records found"
        if a_records:
            ip = a_records[0]
            octets = ip.split(".")
            if len(octets) == 4:
                arpa_name = f"{octets[3]}.{octets[2]}.{octets[1]}.{octets[0]}.in-addr.arpa"
                ptr_records = await self._query_doh(arpa_name, "PTR")
                if ptr_records:
                    ptr_valid = True
                    ptr_record = ptr_records[0].rstrip(".")
                    ptr_status = f"Configured ({ptr_record})"
                    score += 5
                else:
                    ptr_status = f"No PTR for {ip}"
            else:
                ptr_status = f"IP format unrecognized ({ip})"

        # 6. Inspect BIMI Record (Brand Indicators for Message Identification)
        bimi_records = await self._query_doh(f"default._bimi.{clean_d}", "TXT")
        bimi_record = next((r for r in bimi_records if r.startswith("v=BIMI1")), None)
        if bimi_record:
            bimi_valid = True
            bimi_status = "Active (Verified Brand Indicator Published)"
            score += 5
        else:
            bimi_valid = False
            bimi_status = "No BIMI record (Optional for brand avatar)"

        # 7. Inspect MTA-STS (RFC 8461 SMTP Strict Transport Security)
        mta_sts_txt = await self._query_doh(f"_mta-sts.{clean_d}", "TXT")
        mta_sts_record = next((r for r in mta_sts_txt if r.startswith("v=STSv1")), None)
        if mta_sts_record:
            mta_sts_valid = True
            mta_sts_status = "Active (STSv1 Enforced)"
            score += 5
        else:
            mta_sts_valid = False
            mta_sts_status = "No MTA-STS record (Optional for SMTP TLS enforcement)"

        # 8. Inspect TLS-RPT (RFC 8460 SMTP TLS Reporting)
        tls_rpt_txt = await self._query_doh(f"_smtp._tlsrpt.{clean_d}", "TXT")
        tls_rpt_record = next((r for r in tls_rpt_txt if r.startswith("v=TLSRPTv1")), None)
        if tls_rpt_record:
            tls_rpt_valid = True
            tls_rpt_status = "Active (TLSRPTv1 Configured)"
            score += 5
        else:
            tls_rpt_valid = False
            tls_rpt_status = "No TLS-RPT record (Optional for TLS reporting)"

        # 9. Inspect DANE / TLSA (RFC 6698 / RFC 7672 SMTP Certificate Pinning)
        dane_valid = False
        dane_record = None
        tlsa_host = f"_25._tcp.{clean_d}"
        if mx_records:
            first_mx = mx_records[0].split()[-1].rstrip(".")
            tlsa_host = f"_25._tcp.{first_mx}"

        tlsa_records = await self._query_doh(tlsa_host, "TLSA")
        if tlsa_records:
            dane_valid = True
            dane_record = tlsa_records[0]
            dane_status = f"Active ({dane_record[:20]}...)"
            score += 5
        else:
            dane_status = "No DANE TLSA record (Optional for high-security pinning)"

        # 10. Inspect ARC (RFC 8617 Authenticated Received Chain)
        arc_found: List[str] = []
        for sel in self.COMMON_ARC_SELECTORS:
            arc_res = await self._query_doh(f"{sel}._domainkey.{clean_d}", "TXT")
            if any("v=DKIM1" in r or "k=rsa" in r or "p=" in r for r in arc_res):
                arc_found.append(sel)

        if arc_found:
            arc_valid = True
            arc_status = f"Configured ({', '.join(arc_found)})"
            score += 5
        else:
            arc_valid = False
            arc_status = "No ARC selector found (Optional for relay authentication)"

        # 11. Inspect Real-Time DNSBL Reputation (Spamhaus, Barracuda, SpamCop)
        dnsbl_listings: List[str] = []
        probe_ips: List[str] = []
        if a_records:
            probe_ips.append(a_records[0])

        for p_ip in probe_ips:
            octs = p_ip.split(".")
            if len(octs) == 4:
                rev_ip = f"{octs[3]}.{octs[2]}.{octs[1]}.{octs[0]}"
                for zone in self.DNSBL_ZONES:
                    dnsbl_query = f"{rev_ip}.{zone}"
                    bl_res = await self._query_doh(dnsbl_query, "A")
                    if bl_res and any(r.startswith("127.0.0.") for r in bl_res):
                        dnsbl_listings.append(zone.split(".")[0].capitalize())

        if dnsbl_listings:
            dnsbl_listed = True
            dnsbl_status = f"LISTED on {', '.join(dnsbl_listings)} (Immediate spam risk)"
            score = max(0, score - 30)
            recommendations.append(
                f"Your IP is blacklisted on {', '.join(dnsbl_listings)}. Request delisting."
            )
        else:
            dnsbl_listed = False
            dnsbl_status = "Clean (Not listed on major DNSBLs)"

        # 12. Inspect S/MIME & OpenPGP End-to-End Cryptographic Discovery
        smimea_records = await self._query_doh(f"_smimecert.{clean_d}", "TXT")
        openpgp_records = await self._query_doh(f"_openpgpkey.{clean_d}", "TXT")
        if smimea_records or openpgp_records:
            crypto_discovery_valid = True
            kinds: List[str] = []
            if smimea_records:
                kinds.append("S/MIME")
            if openpgp_records:
                kinds.append("OpenPGP")
            crypto_discovery_status = f"Active ({', '.join(kinds)} published)"
            score += 5
        else:
            crypto_discovery_valid = False
            crypto_discovery_status = "No S/MIME or OpenPGP discovery published"

        score = min(100, score)

        return DnsInspectionResult(
            domain=clean_d,
            score=score,
            spf_valid=spf_valid,
            spf_record=spf_record,
            spf_status=spf_status,
            spf_lookup_count=spf_lookup_count,
            dmarc_valid=dmarc_valid,
            dmarc_record=dmarc_record,
            dmarc_status=dmarc_status,
            dkim_valid=dkim_valid,
            dkim_selectors_found=dkim_found,
            dkim_status=dkim_status,
            mx_valid=mx_valid,
            mx_records=mx_records,
            mx_status=mx_status,
            mx_ipv6_valid=mx_ipv6_valid,
            null_mx_declared=null_mx_declared,
            ptr_valid=ptr_valid,
            ptr_record=ptr_record,
            ptr_status=ptr_status,
            bimi_valid=bimi_valid,
            bimi_record=bimi_record,
            bimi_status=bimi_status,
            mta_sts_valid=mta_sts_valid,
            mta_sts_status=mta_sts_status,
            tls_rpt_valid=tls_rpt_valid,
            tls_rpt_status=tls_rpt_status,
            dane_valid=dane_valid,
            dane_record=dane_record,
            dane_status=dane_status,
            arc_valid=arc_valid,
            arc_status=arc_status,
            dnsbl_listed=dnsbl_listed,
            dnsbl_listings=dnsbl_listings,
            dnsbl_status=dnsbl_status,
            crypto_discovery_valid=crypto_discovery_valid,
            crypto_discovery_status=crypto_discovery_status,
            recommendations=recommendations,
        )
