from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EmailLink:
    text: str
    url: str


@dataclass
class EmailPayload:
    title: str
    body_text: str
    recipient_name: Optional[str] = None
    sender_name: Optional[str] = None
    links: List[EmailLink] = field(default_factory=list)
