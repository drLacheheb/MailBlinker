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
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; font-size: 14px; line-height: 1.5; color: #222222; margin: 0; padding: 0; direction: {{ direction|default('ltr') }};">
  <div style="direction: {{ direction|default('ltr') }}; text-align: {{ text_align|default('left') }}; white-space: pre-line;">
{{ payload.body_text }}
  </div>
  {% if payload.links %}
  <div style="margin-top: 12px; direction: {{ direction|default('ltr') }}; text-align: {{ text_align|default('left') }};">
    {% for link in payload.links %}
    <div><a href="{{ link.url }}" style="color: #1a73e8; text-decoration: underline;">{{ link.text }}</a></div>
    {% endfor %}
  </div>
  {% endif %}
  {{ tracking_tags }}
</body>
</html>"""
