GENERAL_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="{{ lang_code|default('en') }}" dir="{{ direction|default('ltr') }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <title>{{ payload.title }}</title>
  <style>
    :root { color-scheme: light dark; supported-color-schemes: light dark; }
    @media (prefers-color-scheme: dark) {
      table[role="presentation"] { background: transparent !important; }
    }
  </style>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans Arabic', 'Noto Sans Hebrew', Arial, sans-serif; line-height: 1.6; color: #2d3748; padding: 16px; direction: {{ direction|default('ltr') }}; text-align: {{ text_align|default('left') }};">
  <div style="max-width: 600px; margin: 0 auto; background: #fff; padding: 20px; direction: {{ direction|default('ltr') }}; text-align: {{ text_align|default('left') }};">
    {% if payload.recipient_name %}
    <p style="margin-top: 0; font-size: 15px;">
      {% if direction == 'rtl' and lang_code == 'he' %}
      שלום {{ payload.recipient_name }},
      {% elif direction == 'rtl' %}
      مرحباً {{ payload.recipient_name }}،
      {% else %}
      Hi {{ payload.recipient_name }},
      {% endif %}
    </p>
    {% endif %}

    <div style="font-size: 15px; color: #4a5568; margin-bottom: 20px; white-space: pre-line; direction: {{ direction|default('ltr') }}; text-align: {{ text_align|default('left') }};">
{{ payload.body_text }}
    </div>

    {% if payload.links %}
    <div style="margin: 20px 0; padding: 14px; background: #f7fafc; border-inline-start: 4px solid #3182ce; border-left: 4px solid #3182ce; padding-inline-start: 14px;">
      <ul style="margin: 0; padding-inline-start: 20px; padding-left: 20px; font-size: 14px; color: #4a5568;">
        {% for link in payload.links %}
        <li style="margin-bottom: 6px;">
          <a href="{{ link.url }}" style="color: #3182ce; font-weight: 500;">{{ link.text }}</a>
        </li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}

    {% if payload.sender_name %}
    <p style="font-size: 15px; margin-bottom: 4px;">
      {% if direction == 'rtl' and lang_code == 'he' %}
      בברכה,
      {% elif direction == 'rtl' %}
      مع أطيب التحيات،
      {% else %}
      Best regards,
      {% endif %}
    </p>
    <p style="font-size: 15px; font-weight: 600; color: #1a202c;">{{ payload.sender_name }}</p>
    {% endif %}
  </div>

  {{ tracking_tags }}
</body>
</html>"""
