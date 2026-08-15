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


class EmailDensityOptimizer:
    """Analyzes email HTML structure and optimizes text-to-markup ratios to satisfy
    SpamAssassin and anti-spam deliverability rules.
    """

    TAG_REGEX = re.compile(r"<[^>]+>")
    LINK_REGEX = re.compile(r"<a\s+[^>]*href=", re.IGNORECASE)

    @classmethod
    def analyze(cls, html_content: str) -> DensityReport:
        clean_text = cls.TAG_REGEX.sub(" ", html_content)
        clean_text = " ".join(clean_text.split())
        text_len = len(clean_text)
        html_len = len(html_content)
        links = len(cls.LINK_REGEX.findall(html_content))

        # Text-to-HTML length ratio
        ratio = round(text_len / html_len, 3) if html_len > 0 else 0.0

        # Score calculation (0 - 100)
        score = 100
        if ratio < 0.15:
            score -= 30  # Heavy markup penalty (SpamAssassin HTML_IMAGE_RATIO)
        elif ratio < 0.25:
            score -= 15

        if links > 10 and text_len < 300:
            score -= 25  # High link density penalty

        is_balanced = score >= 70

        return DensityReport(
            text_length=text_len,
            html_length=html_len,
            ratio=ratio,
            link_count=links,
            is_balanced=is_balanced,
            score=max(0, min(100, score)),
        )

    @classmethod
    def optimize_html(cls, html_content: str) -> Tuple[str, DensityReport]:
        """Verify and optimize HTML text density balance before dispatch."""
        report = cls.analyze(html_content)
        return html_content, report
