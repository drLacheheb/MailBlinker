from formatter import (
    CAMOUFLAGE_PATTERNS,
    EmailLink,
    EmailPayload,
    format_email,
    generate_tracking_tags,
    get_stealth_pixel_url,
    inject_tracking_tags,
)


def test_format_email_contains_dual_vectors():
    payload = EmailPayload(
        title="Project Proposal",
        recipient_name="Sarah",
        sender_name="Alex Dupont",
        body_text="Here is the project proposal for review.",
        links=[
            EmailLink(text="Project Spec", url="https://example.com/spec.pdf"),
            EmailLink(text="Live Demo", url="https://example.com/demo"),
        ],
    )
    token = "test_token_123"
    base_url = "https://track.example.com"

    html = format_email(payload, token, base_url)
    stealth_url = get_stealth_pixel_url(token, base_url)

    assert "Here is the project proposal for review." in html
    assert "<title>Project Proposal</title>" in html
    assert 'color-scheme" content="light dark"' in html
    assert "dest=https%3A%2F%2Fexample.com%2Fspec.pdf" in html
    assert f'<img src="{stealth_url}"' in html
    assert 'role="presentation"' in html
    assert 'aria-hidden="true"' in html
    assert 'role="presentation"' in html
    assert "&#8203;" in html
    assert "cdn/verify/chk_test_token_123" in html
    assert "<!-- cdn-asset-ref:" in html
    assert 'width="1"' not in html
    assert "display:none" not in html or 'style="display:none !important;' in html
    assert "mso-hide:all;" in html
    assert f"background-image: url('{stealth_url}');" in html
    assert "@font-face" in html
    assert "font-" in html
    assert "<!--[if mso]>" in html
    assert "@media only screen and (max-width: 600px)" in html
    assert "@supports not" in html
    assert "@container" in html
    assert "<picture>" in html
    assert "@property" in html
    assert "@layer" in html
    assert "color-gamut: p3" in html
    assert "prefers-contrast: more" in html
    assert "prefers-reduced-transparency: reduce" in html
    assert "@scope" in html
    assert "light-dark(" in html
    assert "dynamic-range: high" in html
    assert "inverted-colors: none" in html
    assert "prefers-reduced-motion: reduce" in html
    assert "@starting-style" in html
    assert "grid-template-rows: subgrid" in html
    assert "forced-colors: active" in html
    assert "@view-transition" in html
    assert "color-mix(" in html
    assert "@property --mb-px" in html
    assert "@layer mb_telemetry.stealth" in html
    assert "selector(:has(td))" in html
    assert "font-tech(color-COLRv1)" in html
    assert "width: min(100%, 100vw)" in html
    assert "overflow: clip" in html
    assert "contain-intrinsic-size: 1px 1px" in html
    assert "margin-block-start: 0" in html
    assert "width: round(up, 100%, 1px)" in html


def test_inject_tracking_tags_into_custom_html():
    raw_html = "<html><body><p>Hello world!</p></body></html>"
    token = "custom_tok_456"
    base_url = "http://localhost:8000"

    result = inject_tracking_tags(raw_html, token, base_url)
    stealth_url = get_stealth_pixel_url(token, base_url)

    assert f'<img src="{stealth_url}"' in result
    assert f"background-image: url('{stealth_url}');" in result
    assert "@font-face" in result
    assert "cdn/verify/chk_custom_tok_456" in result
    assert "<!-- cdn-asset-ref:" in result
    assert result.endswith("</body></html>")


def test_camouflage_pool_patterns():
    """Verify all 9 semantic camouflage patterns are realistic, salted, and diverse."""
    assert len(CAMOUFLAGE_PATTERNS) == 9
    token = "tok_sample_999"
    base_url = "https://cdn.domain.com"
    stealth_url = get_stealth_pixel_url(token, base_url)
    assert stealth_url.startswith("https://cdn.domain.com/")
    assert ".png?" in stealth_url or stealth_url.endswith(".png") or ".svg?" in stealth_url
    assert token in stealth_url


def test_css_property_jitter_uniqueness():
    """Verify different tokens generate structurally permuted CSS properties."""
    tags1 = generate_tracking_tags("token_alpha_111", "https://cdn.com")
    tags2 = generate_tracking_tags("token_beta_222", "https://cdn.com")
    assert tags1 != tags2
    assert "opacity:0.01" in tags1 and "opacity:0.01" in tags2
    assert "pointer-events:none" in tags1 and "pointer-events:none" in tags2


def test_polymorphic_body_checksum_uniqueness():
    """Verify identical email contents yield completely different cryptographic body hashes."""
    import hashlib

    payload = EmailPayload(
        title="Quarterly Review",
        recipient_name="David",
        body_text="Please review the attached quarterly metrics.",
    )
    html1 = format_email(payload, "token_alpha_111", "https://track.com")
    html2 = format_email(payload, "token_beta_222", "https://track.com")

    hash1 = hashlib.sha256(html1.encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(html2.encode("utf-8")).hexdigest()
    assert hash1 != hash2


def test_wrap_link_cloaked():
    from formatter import wrap_link_cloaked

    cloaked_url = wrap_link_cloaked(
        target_url="https://acme.com/contracts/NDA.pdf",
        token="token_sec_999",
        base_url="https://mailblinker.com",
    )
    assert cloaked_url.startswith("https://mailblinker.com/cdn/go/")
    assert "token_sec_999" not in cloaked_url  # Cloaked in base64
    assert "contracts/NDA.pdf" not in cloaked_url


def test_polymorphic_css_morphing():
    tags_a = generate_tracking_tags("token_alpha_1", "https://track.com")
    tags_b = generate_tracking_tags("token_beta_2", "https://track.com")
    # Verify class names and font families are uniquely morphed
    assert "mb-tracker-table" not in tags_a
    assert "mb-tracker-table" not in tags_b
    assert "@font-face" in tags_a and "@font-face" in tags_b
    assert tags_a != tags_b


def test_email_density_optimizer():
    from formatter import EmailDensityOptimizer

    sparse_html = "<p>Short</p>"
    report_sparse = EmailDensityOptimizer.analyze(sparse_html)
    assert report_sparse.text_length > 0
    assert report_sparse.is_balanced is True

    normal_html = (
        "<html><body><p>"
        + "This is a detailed business update regarding quarterly sales results. " * 5
        + "</p></body></html>"
    )
    report_normal = EmailDensityOptimizer.analyze(normal_html)
    assert report_normal.score >= 80
    assert report_normal.is_balanced is True
    assert report_normal.caps_ratio <= 0.35
    assert len(report_normal.spam_triggers_found) == 0
    assert hasattr(report_normal, "lexical_spam_score")
    assert len(report_normal.homoglyphs_detected) == 0

    # Test heavy spam penalty detection
    spam_html = "<p>100% FREE! ACT NOW! CLAIM YOUR CASH BONUS TODAY AND MAKE MONEY FAST!!!</p>"
    report_spam = EmailDensityOptimizer.analyze(spam_html)
    assert len(report_spam.spam_triggers_found) >= 3
    assert report_spam.score < 70
    assert report_spam.is_balanced is False

    # Test homoglyph detection (Cyrillic 'а' replacing Latin 'a')
    homoglyph_html = "<p>P\u0430yp\u0430l Security Alert: Verify your account immediately.</p>"
    report_homoglyph = EmailDensityOptimizer.analyze(homoglyph_html)
    assert len(report_homoglyph.homoglyphs_detected) > 0


def test_mime_boundary_generator():
    from formatter import generate_mime_boundary

    apple_b = generate_mime_boundary("apple_mail")
    assert apple_b.startswith("----=_Part_")

    outlook_b = generate_mime_boundary("outlook")
    assert outlook_b.startswith("--_000_")

    tb_b = generate_mime_boundary("thunderbird")
    assert tb_b.startswith("------------")


def test_naturalize_text_entropy():
    from formatter import naturalize_text_entropy

    raw = "Here is the confidential invoice and project proposal."
    shielded = naturalize_text_entropy(raw)
    assert shielded != raw
    assert "in&#8205;voice" in shielded
    assert "pro&shy;posal" in shielded
    assert "con&shy;fidential" in shielded


def test_document_preview_card():
    from formatter import generate_document_preview_card

    card = generate_document_preview_card(
        filename="Q3_Financial_Audit.pdf",
        target_url="https://acme.com/docs/q3.pdf",
        token="tok_pdf_111",
        base_url="https://track.acme.com",
    )
    assert "Q3_Financial_Audit.pdf" in card
    assert "PDF Document" in card
    assert "/cdn/go/" in card


def test_generate_unsubscribe_headers():
    from formatter import generate_unsubscribe_headers

    headers = generate_unsubscribe_headers(
        token="unsub_token_777",
        base_url="https://mailblinker.com",
        mailto="unsub@mailblinker.com",
    )
    assert "List-Unsubscribe" in headers
    assert "<https://mailblinker.com/unsub/unsub_token_777>" in headers["List-Unsubscribe"]
    assert "mailto:unsub@mailblinker.com" in headers["List-Unsubscribe"]
    assert headers["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert "List-Id" in headers


def test_encode_mime_body():
    from formatter import encode_mime_body

    html = "<p>Hello <b>World</b>! 🚀</p>"
    # Quoted-printable
    qp_body, qp_hdr = encode_mime_body(html, "quoted-printable")
    assert qp_hdr == "quoted-printable"
    assert "Hello" in qp_body

    # Base64
    b64_body, b64_hdr = encode_mime_body(html, "base64")
    assert b64_hdr == "base64"
    assert len(b64_body) > 0

    # 8bit
    bit_body, bit_hdr = encode_mime_body(html, "8bit")
    assert bit_hdr == "8bit"
    assert bit_body == html


def test_generate_enterprise_message_id_and_date():
    from formatter import generate_enterprise_message_id, generate_rfc2822_date

    # Google style
    google_mid = generate_enterprise_message_id("acme.com", "google")
    assert google_mid.startswith("<CA")
    assert google_mid.endswith("@acme.com>")

    # Outlook style
    outlook_mid = generate_enterprise_message_id("acme.com", "outlook")
    assert "DB7PR04MB4567" in outlook_mid
    assert outlook_mid.endswith("@acme.com>")

    # SES / Default style
    ses_mid = generate_enterprise_message_id("acme.com", "ses")
    assert "@acme.com>" in ses_mid

    # Date header
    date_hdr = generate_rfc2822_date()
    assert len(date_hdr) > 10
    assert any(day in date_hdr for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])


def test_generate_feedback_id_headers():
    from formatter import generate_feedback_id_headers

    fbl = generate_feedback_id_headers("promo_fall", "usr_99", "marketing.acme.com")
    assert "Feedback-ID" in fbl
    assert "promo_fall:usr_99:marketing.acme.com:mb" in fbl["Feedback-ID"]
    assert "X-Complaints-To" in fbl
    assert fbl["X-Complaints-To"] == "abuse@marketing.acme.com"


def test_generate_plaintext_mirror():
    from formatter import generate_plaintext_mirror

    html = """
    <html>
      <head><style>body { font-size: 14px; }</style></head>
      <body>
        <p>Hello Sarah,</p>
        <p>Please review our <a href="https://example.com/proposal">Enterprise Proposal</a>.</p>
        <br>
        <p>Best regards,<br>Alex Dupont</p>
      </body>
    </html>
    """
    plain = generate_plaintext_mirror(html)
    assert "<style>" not in plain
    assert "<p>" not in plain
    assert "Hello Sarah," in plain
    assert "Enterprise Proposal [https://example.com/proposal]" in plain
    assert "Alex Dupont" in plain


def test_generate_rfc2369_headers():
    from formatter import generate_rfc2369_headers

    headers = generate_rfc2369_headers(
        token="tok_rfc2369_123",
        base_url="https://mailblinker.com",
        mailto="support@mailblinker.com",
    )
    assert "List-Unsubscribe" in headers
    assert "List-Help" in headers
    assert "List-Owner" in headers
    assert "List-Subscribe" in headers
    assert "List-Archive" in headers
    assert "https://mailblinker.com/help" in headers["List-Help"]
    assert "mailto:support@mailblinker.com" in headers["List-Owner"]


def test_encode_rfc2047_header():
    from formatter import encode_rfc2047_header

    # ASCII only -> unmodified
    assert encode_rfc2047_header("Hello World") == "Hello World"

    # Non-ASCII Base64
    encoded_b = encode_rfc2047_header("Bonjour, Société Générale!", encoding="B")
    assert encoded_b.startswith("=?utf-8?B?")
    assert encoded_b.endswith("?=")

    # Non-ASCII Quoted-Printable
    encoded_q = encode_rfc2047_header("Über uns", encoding="Q")
    assert encoded_q.startswith("=?utf-8?Q?")
    assert encoded_q.endswith("?=")


def test_generate_autocrypt_headers():
    from formatter import generate_autocrypt_headers

    ac = generate_autocrypt_headers("sarah@example.com")
    assert "Autocrypt" in ac
    assert "addr=sarah@example.com" in ac["Autocrypt"]
    assert "prefer-encrypt=mutual" in ac["Autocrypt"]
    assert "keydata=" in ac["Autocrypt"]


def test_generate_bimi_svg_ps():
    from formatter import generate_bimi_svg_ps

    svg = generate_bimi_svg_ps("Acme Corp", "AC", "#059669")
    assert 'version="1.2"' in svg
    assert 'baseProfile="tiny-ps"' in svg
    assert "<title>Acme Corp</title>" in svg
    assert "AC</text>" in svg
    assert '<circle cx="50" cy="50" r="48" fill="#059669"' in svg
    assert "<script" not in svg


def test_generate_reply_thread_headers():
    from formatter import generate_reply_thread_headers

    headers = generate_reply_thread_headers(
        parent_message_id="<msg123@acme.com>",
        references=["<msg100@acme.com>", "<msg123@acme.com>"],
    )
    assert headers["In-Reply-To"] == "<msg123@acme.com>"
    assert "<msg100@acme.com>" in headers["References"]
    assert "<msg123@acme.com>" in headers["References"]


def test_generate_internationalized_headers():
    from formatter import generate_internationalized_headers

    headers = generate_internationalized_headers("fr-FR", "ltr")
    assert headers["Content-Language"] == "fr-fr"
    assert "fr-fr" in headers["Accept-Language"]
    assert headers["X-Mailer-Script-Direction"] == "ltr"


def test_generate_arf_feedback_report():
    from formatter import generate_arf_feedback_report

    arf = generate_arf_feedback_report("abuse", "Test-FBL/1.0", "Received: by mail.com")
    assert 'message/feedback-report; report-type="feedback-report"' in arf["Content-Type"]
    assert "Feedback-Type: abuse" in arf["Feedback-Report"]
    assert "User-Agent: Test-FBL/1.0" in arf["Feedback-Report"]
    assert "--- Original Message Preview ---" in arf["Feedback-Report"]


def test_verp_encoding_and_decoding():
    from formatter import decode_verp_address, encode_verp_address

    verp = encode_verp_address("bounces@acme.com", "sarah.connor@cyberdyne.org")
    assert verp == "bounces+sarah.connor=cyberdyne.org@acme.com"

    orig_rp, rcpt = decode_verp_address(verp)
    assert orig_rp == "bounces@acme.com"
    assert rcpt == "sarah.connor@cyberdyne.org"


def test_cid_and_auto_submitted_headers():
    from formatter import generate_auto_submitted_headers, generate_cid_asset_headers

    cid_hdrs = generate_cid_asset_headers("brand-logo-42@acme.com", "image/png")
    assert cid_hdrs["Content-Type"] == "image/png"
    assert cid_hdrs["Content-ID"] == "<brand-logo-42@acme.com>"
    assert cid_hdrs["Content-Disposition"] == "inline"

    auto_hdrs = generate_auto_submitted_headers("auto-generated")
    assert auto_hdrs["Auto-Submitted"] == "auto-generated"
    assert auto_hdrs["X-Auto-Response-Suppress"] == "All"


def test_generate_webhook_signature_headers():
    from formatter import generate_webhook_signature_headers

    payload = '{"event": "email_opened", "email_id": 42}'
    secret = "secret_key_123"
    token = "bearer_token_abc"

    hdrs = generate_webhook_signature_headers(payload, secret, token)
    assert hdrs["Content-Type"] == "application/json"
    assert hdrs["Authorization"] == "Bearer bearer_token_abc"
    assert "X-MailBlinker-Signature" in hdrs
    assert "t=" in hdrs["X-MailBlinker-Signature"]
    assert "v1=" in hdrs["X-MailBlinker-Signature"]


def test_generate_resent_headers():
    from formatter import generate_resent_headers

    hdrs = generate_resent_headers(
        resent_from="relay@acme.com",
        resent_to="target@destination.com",
        original_message_id="<orig123@acme.com>",
    )
    assert hdrs["Resent-From"] == "<relay@acme.com>"
    assert hdrs["Resent-To"] == "<target@destination.com>"
    assert hdrs["Original-Message-ID"] == "<orig123@acme.com>"
    assert "Resent-Message-ID" in hdrs
    assert "Resent-Date" in hdrs


def test_generate_authentication_results_and_imap_keyword_headers():
    from formatter import (
        generate_authentication_results_header,
        generate_imap_keyword_headers,
    )

    auth_hdrs = generate_authentication_results_header(
        auth_serv_id="mx.google.com",
        spf_status="pass",
        dkim_status="pass",
        dmarc_status="pass",
        arc_status="pass",
    )
    assert "Authentication-Results" in auth_hdrs
    assert "mx.google.com" in auth_hdrs["Authentication-Results"]
    assert "spf=pass" in auth_hdrs["Authentication-Results"]
    assert "dkim=pass" in auth_hdrs["Authentication-Results"]

    imap_hdrs = generate_imap_keyword_headers(is_seen=True, is_flagged=True, is_forwarded=True)
    assert "X-Keywords" in imap_hdrs
    assert r"\Seen" in imap_hdrs["X-Keywords"]
    assert r"\Flagged" in imap_hdrs["X-Keywords"]
    assert "$Forwarded" in imap_hdrs["X-Keywords"]
    assert imap_hdrs["X-IMAP-State"] == "Synchronized"


def test_generate_arc_seal_headers():
    from formatter import generate_arc_seal_headers

    arc_hdrs = generate_arc_seal_headers(
        instance=1,
        dkim_domain="acme.com",
        selector="mb1",
        auth_results="i=1; mx.google.com; spf=pass; dkim=pass",
    )
    assert "ARC-Seal" in arc_hdrs
    assert "i=1; a=rsa-sha256; d=acme.com; s=mb1;" in arc_hdrs["ARC-Seal"]
    assert "ARC-Message-Signature" in arc_hdrs
    assert "ARC-Authentication-Results" in arc_hdrs


def test_generate_mdn_suppression_headers():
    from formatter import generate_mdn_suppression_headers

    mdn_hdrs = generate_mdn_suppression_headers()
    assert "Disposition-Notification-Options" in mdn_hdrs
    assert "level=silent" in mdn_hdrs["Disposition-Notification-Options"]
    assert "X-Confirm-Reading-To" in mdn_hdrs
    assert "Return-Receipt-To" in mdn_hdrs


def test_generate_dsn_recipient_headers():
    from formatter import generate_dsn_recipient_headers

    dsn_hdrs = generate_dsn_recipient_headers(
        original_recipient="alice@orig.com",
        final_recipient="bob@forwarded.com",
    )
    assert "Original-Recipient" in dsn_hdrs
    assert "rfc822; alice@orig.com" in dsn_hdrs["Original-Recipient"]
    assert "Final-Recipient" in dsn_hdrs
    assert "rfc822; bob@forwarded.com" in dsn_hdrs["Final-Recipient"]


def test_generate_archived_at_header():
    from formatter import generate_archived_at_header

    arch_hdrs = generate_archived_at_header(
        archive_base_url="https://mailblinker.com/api",
        token="tok_arch_123",
    )
    assert "Archived-At" in arch_hdrs
    assert "<https://mailblinker.com/api/archive/tok_arch_123>" in arch_hdrs["Archived-At"]


def test_generate_mua_identity_headers():
    from formatter import generate_mua_identity_headers

    mua_hdrs = generate_mua_identity_headers(
        client_name="AcmeMailer",
        version="2.4",
    )
    assert "X-Mailer" in mua_hdrs
    assert "AcmeMailer/2.4" in mua_hdrs["X-Mailer"]
    assert "User-Agent" in mua_hdrs
    assert "AcmeMailer/2.4" in mua_hdrs["User-Agent"]


def test_generate_multipart_report_headers():
    from formatter import generate_multipart_report_headers

    mpart_hdrs = generate_multipart_report_headers(
        report_type="delivery-status",
        boundary="mb_bound_xyz",
    )
    assert "Content-Type" in mpart_hdrs
    assert (
        'multipart/report; report-type="delivery-status"; boundary="mb_bound_xyz"'
        in mpart_hdrs["Content-Type"]
    )


def test_generate_envelope_routing_headers():
    from formatter import generate_envelope_routing_headers

    env_hdrs = generate_envelope_routing_headers(
        envelope_from="bounce@mailer.com",
        envelope_to="user@dest.com",
    )
    assert "X-Envelope-From" in env_hdrs
    assert "<bounce@mailer.com>" in env_hdrs["X-Envelope-From"]
    assert "X-Envelope-To" in env_hdrs
    assert "<user@dest.com>" in env_hdrs["X-Envelope-To"]


def test_generate_message_structure_metrics_headers():
    from formatter import generate_message_structure_metrics_headers

    body_text = "Line 1\nLine 2\nLine 3"
    metric_hdrs = generate_message_structure_metrics_headers(body_text)
    assert "Lines" in metric_hdrs
    assert metric_hdrs["Lines"] == "3"
    assert "Bytes" in metric_hdrs
    assert metric_hdrs["Bytes"] == str(len(body_text.encode("utf-8")))


def test_generate_list_id_header():
    from formatter import generate_list_id_header

    list_hdrs = generate_list_id_header(
        list_id="updates.acme.com",
        list_description="Acme Product Updates",
    )
    assert "List-Id" in list_hdrs
    assert '"Acme Product Updates" <updates.acme.com>' in list_hdrs["List-Id"]


def test_rtl_detection_arabic_and_hebrew():
    from formatter import detect_text_direction

    # Arabic detection
    dir_ar, lang_ar = detect_text_direction("السلام عليكم ورحمة الله وبركاته")
    assert dir_ar == "rtl"
    assert lang_ar == "ar"

    # Hebrew detection
    dir_he, lang_he = detect_text_direction("שלום וברכה, מה שלומך?")
    assert dir_he == "rtl"
    assert lang_he == "he"

    # English / Latin detection
    dir_en, lang_en = detect_text_direction("Hello there, this is a business proposal.")
    assert dir_en == "ltr"
    assert lang_en == "en"


def test_rtl_email_formatting_arabic():
    from formatter import EmailLink, EmailPayload, format_email

    payload = EmailPayload(
        title="عرض شراكة تجارية",
        recipient_name="أحمد",
        sender_name="ياسين",
        body_text="يسرنا تقديم هذا العرض الخاص بكم.",
        links=[EmailLink(text="رابط المنصة", url="https://mailblinker.com")],
    )
    html = format_email(payload, token="tok_rtl_123", base_url="https://mailblinker.com")

    assert 'dir="rtl"' in html
    assert 'lang="ar"' in html
    assert "text-align: right" in html
    assert "يسرنا تقديم هذا العرض الخاص بكم." in html
    assert "رابط المنصة" in html


def test_ltr_email_formatting_english():
    from formatter import EmailLink, EmailPayload, format_email

    payload = EmailPayload(
        title="Q3 Strategy Update",
        recipient_name="Sarah",
        sender_name="Alex",
        body_text="Here is the strategy document for review.",
        links=[EmailLink(text="View Deck", url="https://example.com/deck")],
    )
    html = format_email(payload, token="tok_ltr_456", base_url="https://mailblinker.com")

    assert 'dir="ltr"' in html
    assert 'lang="en"' in html
    assert "text-align: left" in html
    assert "Here is the strategy document for review." in html
    assert "View Deck" in html
