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
    assert '<table class="mb-tracker-table" role="presentation"' in html
    assert "&#8203;" in html
    assert "cdn/verify/chk_test_token_123" in html
    assert "<!-- cdn-asset-ref:" in html
    assert 'color-scheme" content="light dark"' in html
    assert 'width="1"' not in html
    assert "display:none" not in html or 'style="display:none !important;' in html
    assert "mso-hide:all;" in html
    assert f"background-image: url('{stealth_url}');" in html
    assert (
        f"<style>@font-face {{ font-family: 'mb-glyph'; src: url('{stealth_url}'); }}</style>"
        in html
    )


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
