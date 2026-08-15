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

    assert "Project Proposal" in html
    assert "Sarah" in html
    assert "Alex Dupont" in html
    assert "dest=https%3A%2F%2Fexample.com%2Fspec.pdf" in html
    assert f'<img src="{stealth_url}"' in html
    assert 'role="presentation"' in html
    assert 'aria-hidden="true"' in html
    assert 'role="presentation"' in html
    assert "&#8203;" in html
    assert "cdn/verify/chk_test_token_123" in html
    assert "<!-- cdn-asset-ref:" in html
    assert 'color-scheme" content="light dark"' in html
    assert 'width="1"' not in html
    assert "display:none" not in html or 'style="display:none !important;' in html
    assert "mso-hide:all;" in html
    assert f"background-image: url('{stealth_url}');" in html
    assert "@font-face" in html
    assert "font-" in html
    assert "<!--[if mso]>" in html
    assert "@media only screen and (max-width: 600px)" in html
    assert "@supports not" in html


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
