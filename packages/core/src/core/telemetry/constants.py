from typing import List, Tuple

KNOWN_PROXIES: List[Tuple[str, str]] = [
    ("googleimageproxy", "Google Image Proxy (Gmail)"),
    ("apple-mail-privacy-protection", "Apple Mail Privacy Protection"),
    ("safelinks", "Microsoft Defender SafeLinks"),
    ("yahoo", "Yahoo Mail Proxy"),
    ("fastmail", "Fastmail Image Proxy"),
    ("proton", "Proton Mail Image Proxy"),
    ("duckduckgo", "DuckDuckGo Email Protection"),
    ("hey.com", "HEY Email Privacy Proxy"),
]

KNOWN_SECURITY_BOTS: List[str] = [
    "mimecast",
    "proofpoint",
    "barracuda",
    "trendmicro",
    "sophos",
    "symantec",
    "messagelabs",
    "fireeye",
    "ironport",
    "forcepoint",
    "cisco",
    "mcafee",
    "checkpoint",
    "fortinet",
    "palo alto",
    "cyren",
    "virustotal",
    "urlscan",
    "anyrun",
    "hybrid-analysis",
    "cuckoosandbox",
]
