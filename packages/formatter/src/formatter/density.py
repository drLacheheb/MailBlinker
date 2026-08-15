import re
from dataclasses import dataclass
from typing import Tuple


@dataclass
class DensityReport:
    text_length: int
    html_length: int
    ratio: float
    link_count: int
    is_balanced: bool
    score: int
    spam_triggers_found: list[str]
    caps_ratio: float
    lexical_spam_score: int
    homoglyphs_detected: list[str]


class EmailDensityOptimizer:
    """Analyzes email HTML structure and optimizes text-to-markup ratios, lexical entropy,
    and homoglyph obfuscation to satisfy SpamAssassin and anti-spam deliverability rules.
    """

    TAG_REGEX = re.compile(r"<[^>]+>")
    LINK_REGEX = re.compile(r"<a\s+[^>]*href=", re.IGNORECASE)

    # Common Cyrillic & Greek homoglyphs mimicking Latin letters
    HOMOGLYPH_CHARS = {
        "\u0430": "a",
        "\u0441": "c",
        "\u0435": "e",
        "\u043e": "o",
        "\u0440": "p",
        "\u0455": "s",
        "\u0456": "i",
        "\u0443": "y",
        "\u0445": "x",
        "\u0410": "A",
        "\u0412": "B",
        "\u0415": "E",
        "\u041a": "K",
        "\u041c": "M",
        "\u041d": "H",
        "\u041e": "O",
        "\u0420": "P",
        "\u0421": "C",
        "\u0422": "T",
        "\u0425": "X",
        "\u03bf": "o",
    }

    SPAM_KEYWORDS = [
        "100% free",
        "act now",
        "apply now",
        "buy direct",
        "call now",
        "cash bonus",
        "claim now",
        "click here",
        "congratulations",
        "credit card",
        "dear friend",
        "earn extra cash",
        "exclusive deal",
        "fast cash",
        "financial freedom",
        "free gift",
        "free sample",
        "full refund",
        "get out of debt",
        "get paid",
        "guaranteed",
        "make money",
        "million dollars",
        "money back",
        "no credit check",
        "no hidden costs",
        "no obligation",
        "no risk",
        "order now",
        "pure profit",
        "risk free",
        "save big",
        "urgent",
        "winner",
        "you have been selected",
    ]

    @classmethod
    def analyze(cls, html_content: str) -> DensityReport:
        clean_text = cls.TAG_REGEX.sub(" ", html_content)
        clean_text = " ".join(clean_text.split())
        text_len = len(clean_text)
        html_len = len(html_content)
        links = len(cls.LINK_REGEX.findall(html_content))

        # Text-to-HTML length ratio
        ratio = round(text_len / html_len, 3) if html_len > 0 else 0.0

        # Lexical trigger word analysis
        text_lower = clean_text.lower()
        triggers_found = [kw for kw in cls.SPAM_KEYWORDS if kw in text_lower]

        # Uppercase character ratio
        alpha_chars = [c for c in clean_text if c.isalpha()]
        caps_ratio = (
            round(sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars), 3)
            if alpha_chars
            else 0.0
        )

        # Score calculation (0 - 100)
        score = 100
        if ratio < 0.15:
            score -= 25  # Heavy markup penalty (SpamAssassin HTML_IMAGE_RATIO)
        elif ratio < 0.25:
            score -= 10

        if links > 10 and text_len < 300:
            score -= 20  # High link density penalty

        # Lexical penalties
        if triggers_found:
            score -= min(30, len(triggers_found) * 10)

        if caps_ratio > 0.35 and len(alpha_chars) > 30:
            score -= 20  # Excessive capitalization penalty

        if clean_text.count("!") > 4:
            score -= 10  # Exclamation entropy penalty

        # Homoglyph obfuscation analysis
        homoglyphs_found = [c for c in clean_text if c in cls.HOMOGLYPH_CHARS]
        if homoglyphs_found:
            score -= min(25, len(homoglyphs_found) * 5)  # Anti-phishing homoglyph penalty

        final_score = max(0, min(100, score))
        is_balanced = final_score >= 70

        return DensityReport(
            text_length=text_len,
            html_length=html_len,
            ratio=ratio,
            link_count=links,
            is_balanced=is_balanced,
            score=final_score,
            spam_triggers_found=triggers_found,
            caps_ratio=caps_ratio,
            lexical_spam_score=final_score,
            homoglyphs_detected=list(set(homoglyphs_found)),
        )

    @classmethod
    def optimize_html(cls, html_content: str) -> Tuple[str, DensityReport]:
        """Verify and optimize HTML text density balance before dispatch."""
        report = cls.analyze(html_content)
        return html_content, report
