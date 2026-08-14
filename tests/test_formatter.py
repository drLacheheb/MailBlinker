from formatter import EmailLink, EmailPayload, format_email, inject_tracking_tags


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

    assert "Project Proposal" in html
    assert "Sarah" in html
    assert "Alex Dupont" in html
    assert "https://example.com/spec.pdf" in html
    assert '<img src="https://track.example.com/track/test_token_123.gif"' in html
    assert 'style="display:none !important;' in html
    assert "mso-hide:all;" in html
    assert "background-image: url('https://track.example.com/track/test_token_123.gif');" in html


def test_inject_tracking_tags_into_custom_html():
    raw_html = "<html><body><p>Hello world!</p></body></html>"
    token = "custom_tok_456"
    base_url = "http://localhost:8000"

    result = inject_tracking_tags(raw_html, token, base_url)

    assert '<img src="http://localhost:8000/track/custom_tok_456.gif"' in result
    assert "background-image: url('http://localhost:8000/track/custom_tok_456.gif');" in result
    assert result.endswith("</body></html>")
