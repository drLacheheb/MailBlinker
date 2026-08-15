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
    mx_icon = "✅" if res.mx_valid else "❌"
    ptr_icon = "✅" if res.ptr_valid else "❌"
    bimi_icon = "✅" if res.bimi_valid else "ℹ️"
    mta_icon = "✅" if res.mta_sts_valid else "ℹ️"
    tls_rpt_icon = "✅" if res.tls_rpt_valid else "ℹ️"
    dane_icon = "✅" if res.dane_valid else "ℹ️"

    lines = [
        f"{status_icon} <b>Deliverability Score: {res.score}/100</b>",
        f"🌐 <b>Domain:</b> <code>{html.escape(res.domain)}</code>\n",
        f"{spf_icon} <b>SPF:</b> {html.escape(res.spf_status)}",
        f"{dmarc_icon} <b>DMARC:</b> {html.escape(res.dmarc_status)}",
        f"{dkim_icon} <b>DKIM:</b> {html.escape(res.dkim_status)}",
        f"{mx_icon} <b>MX:</b> {html.escape(res.mx_status)}",
        f"{ptr_icon} <b>Reverse DNS (rDNS/PTR):</b> {html.escape(res.ptr_status)}",
        f"{bimi_icon} <b>BIMI Brand Avatar:</b> {html.escape(res.bimi_status)}",
        f"{mta_icon} <b>MTA-STS (SMTP TLS):</b> {html.escape(res.mta_sts_status)}",
        f"{tls_rpt_icon} <b>TLS-RPT (Reporting):</b> {html.escape(res.tls_rpt_status)}",
        f"{dane_icon} <b>DANE / TLSA Pinning:</b> {html.escape(res.dane_status)}\n",
    ]

    if res.recommendations:
        lines.append("💡 <b>Recommended Fixes:</b>")
        for rec in res.recommendations:
            lines.append(f"• {html.escape(rec)}")

    report_text = "\n".join(lines)
    await wait_msg.edit_text(report_text, parse_mode="HTML")
