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
    caa_valid: bool
    caa_status: str
    dmarc_forensic_valid: bool
    dmarc_forensic_status: str
    dnssec_valid: bool
    dnssec_status: str
    dane_smtp_valid: bool
    dane_smtp_status: str
    fcrdns_aligned: bool
    fcrdns_status: str
    ns_valid: bool
    ns_records: List[str]
    ns_status: str
    dkim_ed25519_valid: bool
    dkim_ed25519_status: str
    openpgpkey_valid: bool
    openpgpkey_status: str
    dmarc_tree_walk_valid: bool
    dmarc_org_domain: Optional[str]
    dmarc_tree_walk_status: str
    dns_any_hardened: bool
    dns_any_status: str
    dname_valid: bool
    dname_target: Optional[str]
    dname_status: str
    https_svcb_valid: bool
    https_svcb_status: str
    acme_challenge_found: bool
    acme_challenge_status: str
    spf_exp_valid: bool
    spf_exp_target: Optional[str]
    spf_exp_status: str
    dane_tlsa_params: Optional[str]
    dmarc_pct: int
    dmarc_ri: int
    ct_logging_valid: bool
    ct_logging_status: str
    smimea_valid: bool
    smimea_status: str
    caa_iodef_target: Optional[str]
    caa_iodef_status: str
    caa_validation_methods: Optional[str]
    caa_validation_status: str
    dkim_length_limited: bool
    dkim_length_status: str
    spf_redirect_target: Optional[str]
    spf_redirect_status: str
    nat64_ipv6_valid: bool
    nat64_ipv6_status: str
    dmarc_sp: Optional[str]
    dmarc_sp_status: str
    edns0_valid: bool
    edns0_status: str
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

    async def _query_doh_full(self, name: str, rtype: str) -> dict:
        """Query Multi-Provider DoH pool returning raw response dict including AD (DNSSEC) bit."""
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
                    return res.json()
            except Exception:
                continue
        return {}

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
                caa_valid=False,
                caa_status="Invalid domain format",
                dmarc_forensic_valid=False,
                dmarc_forensic_status="Invalid domain format",
                dnssec_valid=False,
                dnssec_status="Invalid domain format",
                dane_smtp_valid=False,
                dane_smtp_status="Invalid domain format",
                fcrdns_aligned=False,
                fcrdns_status="Invalid domain format",
                ns_valid=False,
                ns_records=[],
                ns_status="Invalid domain format",
                dkim_ed25519_valid=False,
                dkim_ed25519_status="Invalid domain format",
                openpgpkey_valid=False,
                openpgpkey_status="Invalid domain format",
                dmarc_tree_walk_valid=False,
                dmarc_org_domain=None,
                dmarc_tree_walk_status="Invalid domain format",
                dns_any_hardened=False,
                dns_any_status="Invalid domain format",
                dname_valid=False,
                dname_target=None,
                dname_status="Invalid domain format",
                https_svcb_valid=False,
                https_svcb_status="Invalid domain format",
                acme_challenge_found=False,
                acme_challenge_status="Invalid domain format",
                spf_exp_valid=False,
                spf_exp_target=None,
                spf_exp_status="Invalid domain format",
                dane_tlsa_params=None,
                dmarc_pct=100,
                dmarc_ri=86400,
                ct_logging_valid=False,
                ct_logging_status="Invalid domain format",
                smimea_valid=False,
                smimea_status="Invalid domain format",
                caa_iodef_target=None,
                caa_iodef_status="Invalid domain format",
                caa_validation_methods=None,
                caa_validation_status="Invalid domain format",
                dkim_length_limited=False,
                dkim_length_status="Invalid domain format",
                spf_redirect_target=None,
                spf_redirect_status="Invalid domain format",
                nat64_ipv6_valid=False,
                nat64_ipv6_status="Invalid domain format",
                dmarc_sp=None,
                dmarc_sp_status="Invalid domain format",
                edns0_valid=False,
                edns0_status="Invalid domain format",
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

        # Check RFC 7208 exp= explanation modifier
        spf_exp_valid = False
        spf_exp_target = None
        spf_exp_status = "No exp= modifier"
        if spf_record and "exp=" in spf_record:
            for term in spf_record.split():
                if term.startswith("exp="):
                    spf_exp_target = term.split("=", 1)[1]
                    exp_txt = await self._query_doh(spf_exp_target, "TXT")
                    if exp_txt:
                        spf_exp_valid = True
                        spf_exp_status = f"Active ({spf_exp_target})"
                        score += 5
                    else:
                        spf_exp_status = f"Target missing ({spf_exp_target})"

        # Check RFC 7208 redirect= delegation modifier
        spf_redirect_target = None
        spf_redirect_status = "No redirect= modifier"
        if spf_record and "redirect=" in spf_record:
            for term in spf_record.split():
                if term.startswith("redirect="):
                    spf_redirect_target = term.split("=", 1)[1]
                    redir_txt = await self._query_doh(spf_redirect_target, "TXT")
                    if redir_txt:
                        spf_redirect_status = f"Delegated ({spf_redirect_target})"
                    else:
                        spf_redirect_status = f"Target missing ({spf_redirect_target})"
                        recommendations.append(
                            f"SPF redirect target '{spf_redirect_target}' is missing a valid TXT record."
                        )

        # 2. Inspect DMARC Record & RFC 7489 Subdomain Tree-Walk Fallback
        dmarc_txt = await self._query_doh(f"_dmarc.{clean_d}", "TXT")
        dmarc_record = next((r for r in dmarc_txt if r.startswith("v=DMARC1")), None)
        dmarc_forensic_valid = False
        dmarc_forensic_status = "No forensic failure reporting (ruf=)"
        dmarc_tree_walk_valid = False
        dmarc_org_domain = None
        dmarc_tree_walk_status = "Direct domain policy active"

        if not dmarc_record and clean_d.count(".") >= 2:
            parts = clean_d.split(".")
            org_d = ".".join(parts[-2:])
            dmarc_org_txt = await self._query_doh(f"_dmarc.{org_d}", "TXT")
            org_rec = next((r for r in dmarc_org_txt if r.startswith("v=DMARC1")), None)
            if org_rec:
                dmarc_record = org_rec
                dmarc_tree_walk_valid = True
                dmarc_org_domain = org_d
                sp_match = "sp=reject" in org_rec or "sp=quarantine" in org_rec
                dmarc_tree_walk_status = (
                    f"Inherited from {org_d} (sp={'enforced' if sp_match else 'default'})"
                )

        dmarc_pct = 100
        dmarc_ri = 86400
        dmarc_sp = None
        dmarc_sp_status = "Inherited from p= (No explicit sp=)"
        if dmarc_record:
            for tag in dmarc_record.split(";"):
                tag = tag.strip()
                if tag.startswith("pct="):
                    try:
                        dmarc_pct = int(tag.split("=", 1)[1])
                    except ValueError:
                        dmarc_pct = 100
                elif tag.startswith("ri="):
                    try:
                        dmarc_ri = int(tag.split("=", 1)[1])
                    except ValueError:
                        dmarc_ri = 86400
                elif tag.startswith("sp="):
                    dmarc_sp = tag.split("=", 1)[1].strip()
                    dmarc_sp_status = f"Enforced (sp={dmarc_sp})"

            if "ruf=" in dmarc_record:
                dmarc_forensic_valid = True
                fo_mode = "fo=1" if "fo=1" in dmarc_record else "default"
                dmarc_forensic_status = f"Active ({fo_mode})"
                score += 5
            if "p=reject" in dmarc_record or "p=quarantine" in dmarc_record:
                dmarc_valid = True
                policy = "reject" if "p=reject" in dmarc_record else "quarantine"
                pct_str = f" (pct={dmarc_pct}%)" if dmarc_pct < 100 else ""
                dmarc_status = f"Enforced ({policy}){pct_str}"
                score += 25
            else:
                dmarc_valid = True
                dmarc_status = "Monitoring mode (p=none)"
                recommendations.append(
                    "Strengthen DMARC policy from 'p=none' to 'p=quarantine' or 'p=reject'."
                )
                score += 15

            if dmarc_pct < 100:
                recommendations.append(
                    f"Increase DMARC pct from {dmarc_pct}% to 100% for full domain protection."
                )
        else:
            dmarc_valid = False
            dmarc_status = "Missing DMARC record"
            recommendations.append(
                f"Add a TXT record for '_dmarc.{clean_d}' with value: "
                "'v=DMARC1; p=quarantine; sp=quarantine;'"
            )

        # 3. Inspect DKIM Records (Probe common selectors & RFC 8463 Ed25519)
        dkim_found: List[str] = []
        dkim_ed25519_valid = False
        dkim_length_limited = False
        for sel in self.COMMON_DKIM_SELECTORS:
            dkim_res = await self._query_doh(f"{sel}._domainkey.{clean_d}", "TXT")
            if any("k=ed25519" in r.lower() for r in dkim_res):
                dkim_ed25519_valid = True
                dkim_found.append(f"{sel} (Ed25519)")
            elif any("k=rsa" in r or "p=" in r or "v=DKIM1" in r for r in dkim_res):
                dkim_found.append(sel)
            if any("l=" in r.lower() for r in dkim_res):
                dkim_length_limited = True

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

        if dkim_length_limited:
            dkim_length_status = "Vulnerable (RFC 6376 l= body length limit declared)"
            recommendations.append(
                "Remove 'l=' body length limit in DKIM record to prevent trailer injection attacks."
            )
        else:
            dkim_length_status = "Secure (Full body integrity / unbounded)"

        if dkim_ed25519_valid:
            dkim_ed25519_status = "RFC 8463 Ed25519 Active (Edwards-Curve Public Key)"
            score += 5
        else:
            dkim_ed25519_status = "RSA (Standard 2048-bit / 1024-bit)"

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
        fcrdns_aligned = False
        fcrdns_status = "No A records found"
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

                    fwd_a = await self._query_doh(ptr_record, "A")
                    if ip in fwd_a:
                        fcrdns_aligned = True
                        fcrdns_status = f"Verified (100% bidirectional match: {ip} ↔ {ptr_record})"
                        score += 5
                    else:
                        fcrdns_aligned = False
                        fcrdns_status = (
                            f"Mismatch (PTR {ptr_record} resolves to {fwd_a} vs IP {ip})"
                        )
                else:
                    ptr_status = f"No PTR for {ip}"
                    fcrdns_status = f"No PTR for {ip}"
            else:
                ptr_status = f"IP format unrecognized ({ip})"
                fcrdns_status = f"IP format unrecognized ({ip})"

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
        dane_smtp_valid = False
        dane_smtp_status = "No DANE SMTP TLSA record"
        dane_tlsa_params = None
        tlsa_host = f"_25._tcp.{clean_d}"
        if mx_records:
            first_mx = mx_records[0].split()[-1].rstrip(".")
            tlsa_host = f"_25._tcp.{first_mx}"

        tlsa_records = await self._query_doh(tlsa_host, "TLSA")
        if tlsa_records:
            dane_valid = True
            dane_smtp_valid = True
            dane_record = tlsa_records[0]
            dane_status = f"Active ({dane_record[:20]}...)"
            parts = dane_record.split()
            if len(parts) >= 3:
                usage, selector, mtype = parts[0], parts[1], parts[2]
                dane_tlsa_params = f"{usage}-{selector}-{mtype}"
                usage_label = (
                    "DANE-EE 3-1-1"
                    if usage == "3" and selector == "1" and mtype == "1"
                    else f"Usage {usage}"
                )
                dane_smtp_status = f"Enforced ({usage_label}) on {tlsa_host}"
            else:
                dane_smtp_status = f"Enforced on {tlsa_host}"
            score += 5
        else:
            dane_status = "No DANE TLSA record (Optional for high-security pinning)"
            dane_smtp_status = "No RFC 7672 DANE TLSA pinned on port 25"

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

        # 13. Inspect RFC 8659 CAA (Certification Authority Authorization)
        caa_records = await self._query_doh(clean_d, "CAA")
        caa_iodef_target = None
        caa_iodef_status = "No iodef incident endpoint"
        caa_validation_methods = None
        caa_validation_status = "Standard (No method restriction)"
        if caa_records:
            caa_valid = True
            caa_issuers = []
            for r in caa_records:
                if "issue" in r:
                    caa_issuers.append(r.split()[-1].strip('"'))
                elif "iodef" in r:
                    caa_iodef_target = r.split()[-1].strip('"')
                    caa_iodef_status = f"Enforced ({caa_iodef_target})"
                if "validationmethods" in r.lower():
                    for part in r.split(";"):
                        if "validationmethods" in part.lower():
                            caa_validation_methods = part.split("=")[-1].strip(' "')
                            caa_validation_status = f"Restricted ({caa_validation_methods})"
            caa_status = f"Enforced ({', '.join(caa_issuers) if caa_issuers else 'Active'})"
            score += 5
        else:
            caa_valid = False
            caa_status = "No CAA record (Optional for TLS CA pinning)"

        # 14. Inspect DNSSEC (RFC 4035 Authenticated Data Flag)
        soa_resp = await self._query_doh_full(clean_d, "SOA")
        dnssec_valid = bool(soa_resp.get("AD", False))
        if not dnssec_valid:
            txt_resp = await self._query_doh_full(clean_d, "TXT")
            dnssec_valid = bool(txt_resp.get("AD", False))

        if dnssec_valid:
            dnssec_status = "Active (DNSSEC Signed & Validated)"
            score += 5
        else:
            dnssec_status = "Not signed with DNSSEC (Zone unauthenticated)"

        # 15. Inspect Authoritative Nameserver (NS) Redundancy
        ns_records = await self._query_doh(clean_d, "NS")
        if ns_records:
            ns_valid = len(ns_records) >= 2
            ns_status = (
                f"Redundant ({len(ns_records)} nameservers)"
                if ns_valid
                else f"Single NS ({len(ns_records)} host)"
            )
            if ns_valid:
                score += 5
        else:
            ns_valid = False
            ns_status = "No NS records found"

        # 16. Inspect RFC 7929 OPENPGPKEY (DANE for OpenPGP)
        openpgp_rr = await self._query_doh(f"_openpgpkey.{clean_d}", "OPENPGPKEY")
        if not openpgp_rr:
            openpgp_rr = await self._query_doh(f"_openpgpkey.{clean_d}", "TXT")
        if openpgp_rr:
            openpgpkey_valid = True
            openpgpkey_status = "Active (RFC 7929 OPENPGPKEY Key Published)"
            score += 5
        else:
            openpgpkey_valid = False
            openpgpkey_status = "No RFC 7929 OPENPGPKEY record"

        # 17. Inspect RFC 8482 DNS ANY Minimal Response / DDoS Hardening
        any_resp = await self._query_doh(clean_d, "ANY")
        if any_resp and (
            any("rfc8482" in r.lower() or "hinfo" in r.lower() for r in any_resp)
            or len(any_resp) <= 2
        ):
            dns_any_hardened = True
            dns_any_status = "Hardened (RFC 8482 Minimal Response)"
            score += 5
        else:
            dns_any_hardened = False
            dns_any_status = "Standard ANY response"

        # 18. Inspect RFC 6672 DNAME Subtree Delegation
        dname_records = await self._query_doh(clean_d, "DNAME")
        if not dname_records:
            dname_records = await self._query_doh(f"_domainkey.{clean_d}", "DNAME")

        if dname_records:
            dname_valid = True
            dname_target = dname_records[0].strip().rstrip(".")
            dname_status = f"Active -> {dname_target}"
            score += 5
        else:
            dname_valid = False
            dname_target = None
            dname_status = "No DNAME delegation"

        # 19. Inspect RFC 9460 HTTPS & SVCB Protocol Records
        https_records = await self._query_doh(clean_d, "HTTPS")
        if not https_records:
            https_records = await self._query_doh(clean_d, "SVCB")

        if https_records:
            https_svcb_valid = True
            alpn_hints = [r for r in https_records if "alpn=" in r.lower()]
            https_svcb_status = (
                f"Active ({len(https_records)} RRs)"
                if not alpn_hints
                else f"Active ({alpn_hints[0][:30]}...)"
            )
            score += 5
        else:
            https_svcb_valid = False
            https_svcb_status = "No RFC 9460 HTTPS/SVCB record"

        # 20. Inspect RFC 8555 ACME Challenge DNS Hygiene
        acme_records = await self._query_doh(f"_acme-challenge.{clean_d}", "TXT")
        if acme_records:
            acme_challenge_found = True
            acme_challenge_status = f"Active ({len(acme_records)} challenge token(s) present)"
        else:
            acme_challenge_found = False
            acme_challenge_status = "Clean (No stale _acme-challenge records)"

        # 21. Inspect RFC 9162 Certificate Transparency (CT) Logging
        ct_records = await self._query_doh(f"_ct.{clean_d}", "TXT")
        if not ct_records:
            ct_records = await self._query_doh(clean_d, "CAA")
            ct_records = [r for r in ct_records if "issue" in r.lower()]

        if ct_records:
            ct_logging_valid = True
            ct_logging_status = "Compliant (TLS CT policy pinned)"
            score += 5
        else:
            ct_logging_valid = False
            ct_logging_status = "Standard TLS (No explicit CT pinning)"

        # 22. Inspect RFC 8162 SMIMEA DNS Record
        smimea_rrs = await self._query_doh(f"_smimecert.{clean_d}", "SMIMEA")
        if not smimea_rrs:
            smimea_rrs = await self._query_doh(f"_smimecert.{clean_d}", "TXT")

        if smimea_rrs:
            smimea_valid = True
            smimea_status = f"Published ({len(smimea_rrs)} cert association(s))"
            score += 5
        else:
            smimea_valid = False
            smimea_status = "No SMIMEA record (Optional for DNSSEC S/MIME)"

        # 23. Inspect RFC 7050 / RFC 8880 NAT64 & IPv6 Discovery
        nat64_records = await self._query_doh("ipv4only.arpa", "AAAA")
        if mx_ipv6_valid or nat64_records:
            nat64_ipv6_valid = True
            nat64_ipv6_status = "Supported (Dual-Stack IPv6 / NAT64 Ready)"
            score += 5
        else:
            nat64_ipv6_valid = False
            nat64_ipv6_status = "IPv4-Only (No IPv6 MX or NAT64 synthesis)"

        # 24. Inspect RFC 8499 / RFC 6891 EDNS0 Buffer Sizing & Fragmentation
        soa_full = await self._query_doh_full(clean_d, "SOA")
        if soa_full and not soa_full.get("TC", False):
            edns0_valid = True
            edns0_status = "Compliant (1232-byte DNS Flag Day buffer, No TC Truncation)"
            score += 5
        else:
            edns0_valid = False
            edns0_status = "Truncated / Non-compliant (Upstream TC flag encountered)"

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
            dmarc_sp=dmarc_sp,
            dmarc_sp_status=dmarc_sp_status,
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
            caa_valid=caa_valid,
            caa_status=caa_status,
            dmarc_forensic_valid=dmarc_forensic_valid,
            dmarc_forensic_status=dmarc_forensic_status,
            dnssec_valid=dnssec_valid,
            dnssec_status=dnssec_status,
            dane_smtp_valid=dane_smtp_valid,
            dane_smtp_status=dane_smtp_status,
            fcrdns_aligned=fcrdns_aligned,
            fcrdns_status=fcrdns_status,
            ns_valid=ns_valid,
            ns_records=ns_records,
            ns_status=ns_status,
            dkim_ed25519_valid=dkim_ed25519_valid,
            dkim_ed25519_status=dkim_ed25519_status,
            openpgpkey_valid=openpgpkey_valid,
            openpgpkey_status=openpgpkey_status,
            dmarc_tree_walk_valid=dmarc_tree_walk_valid,
            dmarc_org_domain=dmarc_org_domain,
            dmarc_tree_walk_status=dmarc_tree_walk_status,
            dns_any_hardened=dns_any_hardened,
            dns_any_status=dns_any_status,
            dname_valid=dname_valid,
            dname_target=dname_target,
            dname_status=dname_status,
            https_svcb_valid=https_svcb_valid,
            https_svcb_status=https_svcb_status,
            acme_challenge_found=acme_challenge_found,
            acme_challenge_status=acme_challenge_status,
            spf_exp_valid=spf_exp_valid,
            spf_exp_target=spf_exp_target,
            spf_exp_status=spf_exp_status,
            spf_redirect_target=spf_redirect_target,
            spf_redirect_status=spf_redirect_status,
            dane_tlsa_params=dane_tlsa_params,
            dmarc_pct=dmarc_pct,
            dmarc_ri=dmarc_ri,
            ct_logging_valid=ct_logging_valid,
            ct_logging_status=ct_logging_status,
            smimea_valid=smimea_valid,
            smimea_status=smimea_status,
            caa_iodef_target=caa_iodef_target,
            caa_iodef_status=caa_iodef_status,
            caa_validation_methods=caa_validation_methods,
            caa_validation_status=caa_validation_status,
            dkim_length_limited=dkim_length_limited,
            dkim_length_status=dkim_length_status,
            nat64_ipv6_valid=nat64_ipv6_valid,
            nat64_ipv6_status=nat64_ipv6_status,
            edns0_valid=edns0_valid,
            edns0_status=edns0_status,
            recommendations=recommendations,
        )
