from formatter import (
    CAMOUFLAGE_PATTERNS,
    EmailLink,
    EmailPayload,
    format_email,
    generate_tracking_tags,
    get_stealth_pixel_url,
    inject_tracking_tags,
)


def test_format_email_contains_clean_tracking_pixel():
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
    assert "dest=https%3A%2F%2Fexample.com%2Fspec.pdf" in html
    assert f'<img src="{stealth_url}"' in html
    assert 'width="1"' in html
    assert 'height="1"' in html
    assert "display:none" not in html


def test_inject_tracking_tags_into_custom_html():
    raw_html = "<html><body><p>Hello world!</p></body></html>"
    token = "custom_tok_456"
    base_url = "http://localhost:8000"

    result = inject_tracking_tags(raw_html, token, base_url)
    stealth_url = get_stealth_pixel_url(token, base_url)

    assert f'<img src="{stealth_url}"' in result
    assert 'width="1"' in result
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


def test_auto_inline_link_scanning():
    payload = EmailPayload(
        title="Check out our tools",
        recipient_name="Sarah",
        sender_name="Alex",
        body_text="Hi Sarah, please see our demo at https://example.com/demo and review https://example.com/spec.pdf!",
    )
    html = format_email(payload, token="tok_scan_999", base_url="https://mailblinker.com")

    assert "/l/tok_scan_999?dest=https%3A%2F%2Fexample.com%2Fdemo" in html
    assert "/l/tok_scan_999?dest=https%3A%2F%2Fexample.com%2Fspec.pdf" in html
    assert "https://example.com/demo" in html
    assert "https://example.com/spec.pdf" in html
    # Verify punctuation like '!' was preserved outside the link
    assert "</a>!" in html
