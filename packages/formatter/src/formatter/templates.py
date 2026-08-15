GENERAL_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <title>{{ payload.title }}</title>
  <style>
    :root { color-scheme: light dark; supported-color-schemes: light dark; }
    @media (prefers-color-scheme: dark) {
      .mb-tracker-table { background: transparent !important; }
    }
  </style>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #2d3748; padding: 16px;">
  <div style="max-width: 600px; margin: 0 auto; background: #fff; padding: 20px;">
    {% if payload.recipient_name %}
    <p style="margin-top: 0; font-size: 15px;">
      Hi {{ payload.recipient_name }},
    </p>
    {% endif %}

    <div style="font-size: 15px; color: #4a5568; margin-bottom: 20px; white-space: pre-line;">
{{ payload.body_text }}
    </div>

    {% if payload.links %}
    <div style="margin: 20px 0; padding: 14px; background: #f7fafc; border-left: 4px solid #318;">
      <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #4a5568;">
        {% for link in payload.links %}
        <li style="margin-bottom: 6px;">
          <a href="{{ link.url }}" style="color: #3182ce; font-weight: 500;">{{ link.text }}</a>
        </li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

    {% if payload.sender_name %}
    <p style="font-size: 15px; margin-bottom: 4px;">Best regards,</p>
    <p style="font-size: 15px; font-weight: 600; color: #1a202c;">{{ payload.sender_name }}</p>
    {% endif %}
  </div>

  {{ tracking_tags }}
</body>
</html>"""
