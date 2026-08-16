import html

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from core import DnsDeliverabilityInspector

from ..keyboards import main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    greeting = "⚡ <b>MailBlinker</b>"
    if message.from_user and message.from_user.first_name:
        greeting = f"⚡ <b>Welcome, {html.escape(message.from_user.first_name)}!</b>"

    text = (
        f"{greeting}\n"
        "Invisible email tracking with instant open alerts.\n\n"
        "Choose an action below to get started:"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
@router.message(F.text == "❓ How to Use")
async def cmd_help(message: types.Message):
    text = (
        "📖 <b>How to Use:</b>\n\n"
        "1. Tap <b>⚡ Fast Track</b> to create your tracker.\n"
        "2. Open the attached <code>.html</code> file in your browser.\n"
        "3. Copy and paste it into your Gmail or Outlook draft.\n"
        "4. When read, you'll receive an instant alert here!"
    )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "No active action to cancel.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.clear()
    await message.answer(
        "Cancelled.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


_dns_inspector = DnsDeliverabilityInspector()


@router.message(Command("check_domain"))
@router.message(Command("dns"))
async def cmd_check_domain(message: types.Message):
    args = message.text.split(maxsplit=1) if message.text else []
    if len(args) < 2:
        await message.answer(
            "🔍 <b>DNS Deliverability Inspector</b>\n\n"
            "Usage: <code>/check_domain &lt;domain_or_email&gt;</code>\n"
            "Example: <code>/check_domain acme.com</code>\n\n"
            "Checks SPF, DMARC, and MX records to calculate your email deliverability score.",
            parse_mode="HTML",
        )
        return

    target_domain = args[1].strip()
    wait_msg = await message.answer(
        f"🔍 Analyzing DNS authentication for <code>{html.escape(target_domain)}</code>...",
        parse_mode="HTML",
    )

    res = await _dns_inspector.inspect(target_domain)

    status_icon = "🟢" if res.score >= 80 else ("🟡" if res.score >= 50 else "🔴")
    spf_icon = "✅" if res.spf_valid else "❌"
    dmarc_icon = "✅" if res.dmarc_valid else "❌"
    dkim_icon = "✅" if res.dkim_valid else "❌"
    mx_icon = "🛡️" if res.null_mx_declared else ("✅" if res.mx_valid else "❌")
    ptr_icon = "✅" if res.ptr_valid else "❌"
    bimi_icon = "✅" if res.bimi_valid else "ℹ️"
    mta_icon = "✅" if res.mta_sts_valid else "ℹ️"
    tls_rpt_icon = "✅" if res.tls_rpt_valid else "ℹ️"
    dane_icon = "✅" if res.dane_valid else "ℹ️"
    arc_icon = "✅" if res.arc_valid else "ℹ️"
    dnsbl_icon = "❌" if res.dnsbl_listed else "✅"
    crypto_icon = "✅" if res.crypto_discovery_valid else "ℹ️"
    caa_icon = "✅" if res.caa_valid else "ℹ️"
    dmarc_fo_icon = "✅" if res.dmarc_forensic_valid else "ℹ️"
    dnssec_icon = "✅" if res.dnssec_valid else "ℹ️"
    fcrdns_icon = "✅" if res.fcrdns_aligned else "ℹ️"
    dane_smtp_icon = "✅" if res.dane_smtp_valid else "ℹ️"
    ns_icon = "✅" if res.ns_valid else "ℹ️"
    ed25519_icon = "✅" if res.dkim_ed25519_valid else "ℹ️"
    openpgpkey_icon = "✅" if res.openpgpkey_valid else "ℹ️"
    tree_walk_icon = "✅" if res.dmarc_tree_walk_valid else "ℹ️"
    any_icon = "✅" if res.dns_any_hardened else "ℹ️"
    dname_icon = "✅" if res.dname_valid else "ℹ️"
    https_icon = "✅" if res.https_svcb_valid else "ℹ️"
    acme_icon = "ℹ️" if res.acme_challenge_found else "✅"
    spf_exp_icon = "✅" if res.spf_exp_valid else "ℹ️"
    ct_icon = "✅" if res.ct_logging_valid else "ℹ️"
    smimea_icon = "✅" if res.smimea_valid else "ℹ️"
    iodef_icon = "✅" if res.caa_iodef_target else "ℹ️"
    caa_val_icon = "✅" if res.caa_validation_methods else "ℹ️"
    dkim_len_icon = "ℹ️" if res.dkim_length_limited else "✅"
    spf_redir_icon = "✅" if res.spf_redirect_target else "ℹ️"
    nat64_icon = "✅" if res.nat64_ipv6_valid else "ℹ️"
    dmarc_sp_icon = "✅" if res.dmarc_sp else "ℹ️"
    edns0_icon = "✅" if res.edns0_valid else "ℹ️"
    spf_ip6_icon = "✅" if res.spf_ip6_valid else "ℹ️"
    uri_rr_icon = "✅" if res.uri_rr_valid else "ℹ️"
    spf_depth = (
        f" ({res.spf_lookup_count}/10 DNS lookups)"
        if res.spf_valid and res.spf_lookup_count > 0
        else ""
    )

    lines = [
        f"{status_icon} <b>Deliverability Score: {res.score}/100</b>",
        f"🌐 <b>Domain:</b> <code>{html.escape(res.domain)}</code>\n",
        f"{spf_icon} <b>SPF:</b> {html.escape(res.spf_status)}{spf_depth}",
        f"{spf_exp_icon} <b>SPF Explanation (exp=):</b> {html.escape(res.spf_exp_status)}",
        f"{spf_redir_icon} <b>SPF Redirect (redirect=):</b> {html.escape(res.spf_redirect_status)}",
        f"{spf_ip6_icon} <b>RFC 7208 SPF IPv6 (ip6:):</b> {html.escape(res.spf_ip6_status)}",
        f"{dmarc_icon} <b>DMARC:</b> {html.escape(res.dmarc_status)}",
        f"{dmarc_sp_icon} <b>DMARC Subdomain (sp=):</b> {html.escape(res.dmarc_sp_status)}",
        f"{tree_walk_icon} <b>DMARC Tree-Walk:</b> {html.escape(res.dmarc_tree_walk_status)}",
        f"{dkim_icon} <b>DKIM:</b> {html.escape(res.dkim_status)}",
        f"{dkim_len_icon} <b>RFC 6376 DKIM Length (l=):</b> {html.escape(res.dkim_length_status)}",
        f"{ed25519_icon} <b>Ed25519 DKIM:</b> {html.escape(res.dkim_ed25519_status)}",
        f"{mx_icon} <b>MX:</b> {html.escape(res.mx_status)}",
        f"{ptr_icon} <b>Reverse DNS (rDNS/PTR):</b> {html.escape(res.ptr_status)}",
        f"{fcrdns_icon} <b>FCrDNS (Bidirectional):</b> {html.escape(res.fcrdns_status)}",
        f"{nat64_icon} <b>RFC 7050 NAT64 / IPv6:</b> {html.escape(res.nat64_ipv6_status)}",
        f"{bimi_icon} <b>BIMI Brand Avatar:</b> {html.escape(res.bimi_status)}",
        f"{mta_icon} <b>MTA-STS (SMTP TLS):</b> {html.escape(res.mta_sts_status)}",
        f"{tls_rpt_icon} <b>TLS-RPT (Reporting):</b> {html.escape(res.tls_rpt_status)}",
        f"{dane_icon} <b>DANE / TLSA Pinning:</b> {html.escape(res.dane_status)}",
        f"{dane_smtp_icon} <b>DANE SMTP (Port 25):</b> {html.escape(res.dane_smtp_status)}",
        f"{arc_icon} <b>ARC (Relay Chain):</b> {html.escape(res.arc_status)}",
        f"{dnsbl_icon} <b>DNSBL IP Reputation:</b> {html.escape(res.dnsbl_status)}",
        f"{crypto_icon} <b>S/MIME & OpenPGP:</b> {html.escape(res.crypto_discovery_status)}",
        f"{openpgpkey_icon} <b>OPENPGPKEY (DANE PGP):</b> {html.escape(res.openpgpkey_status)}",
        f"{smimea_icon} <b>RFC 8162 SMIMEA:</b> {html.escape(res.smimea_status)}",
        f"{caa_icon} <b>CAA (TLS CA Pinning):</b> {html.escape(res.caa_status)}",
        f"{iodef_icon} <b>CAA Incident (iodef):</b> {html.escape(res.caa_iodef_status)}",
        f"{caa_val_icon} <b>RFC 8657 CAA Validation:</b> {html.escape(res.caa_validation_status)}",
        f"{ct_icon} <b>RFC 9162 Certificate Transparency:</b> {html.escape(res.ct_logging_status)}",
        f"{dmarc_fo_icon} <b>DMARC Forensic (ruf):</b> {html.escape(res.dmarc_forensic_status)}",
        f"{dnssec_icon} <b>DNSSEC Zone Signing:</b> {html.escape(res.dnssec_status)}",
        f"{edns0_icon} <b>RFC 8499 EDNS0 Buffer:</b> {html.escape(res.edns0_status)}",
        f"{any_icon} <b>RFC 8482 ANY Hardening:</b> {html.escape(res.dns_any_status)}",
        f"{dname_icon} <b>RFC 6672 DNAME:</b> {html.escape(res.dname_status)}",
        f"{https_icon} <b>RFC 9460 HTTPS/SVCB:</b> {html.escape(res.https_svcb_status)}",
        f"{acme_icon} <b>RFC 8555 ACME DNS:</b> {html.escape(res.acme_challenge_status)}",
        f"{uri_rr_icon} <b>RFC 7553 URI Record:</b> {html.escape(res.uri_rr_status)}",
        f"{ns_icon} <b>Nameservers (NS):</b> {html.escape(res.ns_status)}\n",
    ]

    if res.recommendations:
        lines.append("💡 <b>Recommended Fixes:</b>")
        for rec in res.recommendations:
            lines.append(f"• {html.escape(rec)}")

    report_text = "\n".join(lines)
    await wait_msg.edit_text(report_text, parse_mode="HTML")
