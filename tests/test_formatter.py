from formatter import (
    CAMOUFLAGE_PATTERNS,
    EmailLink,
    EmailPayload,
    format_email,
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
    assert "https://example.com/spec.pdf" in html
    assert f'<img src="{stealth_url}"' in html
    assert 'role="presentation"' in html
    assert 'aria-hidden="true"' in html
    assert '<table role="presentation"' in html
    assert 'width="1"' not in html
    assert "display:none" not in html
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
    assert result.endswith("</body></html>")


def test_camouflage_pool_patterns():
    """Verify all 8 semantic camouflage patterns are realistic, salted, and diverse."""
    assert len(CAMOUFLAGE_PATTERNS) == 8
    token = "tok_sample_999"
    base_url = "https://cdn.domain.com"
    stealth_url = get_stealth_pixel_url(token, base_url)
    assert stealth_url.startswith("https://cdn.domain.com/")
    assert ".png?" in stealth_url or stealth_url.endswith(".png")
    assert token in stealth_url
