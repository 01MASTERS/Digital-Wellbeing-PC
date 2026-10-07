"""Website domain normalization, browser detection, and title parsing."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

BROWSER_APPS = frozenset({
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "brave.exe",
    "opera.exe",
    "opera_gx.exe",
    "vivaldi.exe",
    "arc.exe",
    "waterfox.exe",
})

# Matches valid domain names: example.com, sub.domain.org, etc.
DOMAIN_REGEX = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$",
    re.IGNORECASE,
)

KNOWN_SITE_TITLES: tuple[tuple[str, str], ...] = (
    ("YouTube", "youtube.com"),
    ("Reddit", "reddit.com"),
    ("Twitter", "x.com"),
    (" X ", "x.com"),
    ("GitHub", "github.com"),
    ("Twitch", "twitch.tv"),
    ("Netflix", "netflix.com"),
    ("Facebook", "facebook.com"),
    ("Instagram", "instagram.com"),
    ("LinkedIn", "linkedin.com"),
    ("Amazon", "amazon.com"),
    ("Wikipedia", "wikipedia.org"),
    ("Stack Overflow", "stackoverflow.com"),
    ("ChatGPT", "chatgpt.com"),
    ("Claude", "claude.ai"),
    ("Google Search", "google.com"),
    ("Gmail", "mail.google.com"),
    ("Google Docs", "docs.google.com"),
    ("Google Drive", "drive.google.com"),
    ("Notion", "notion.so"),
    ("Spotify", "spotify.com"),
    ("Discord", "discord.com"),
)


def normalize_domain(domain: str) -> str:
    """Normalize and validate a website domain name.

    Strips leading 'www.' and trailing dots, validates hostname structure,
    and rejects ports, paths, or single-label hostnames like 'localhost'.
    """
    if not isinstance(domain, str):
        raise TypeError("Domain must be a string")
    clean = domain.strip().rstrip(".")
    if not clean:
        raise ValueError("Domain cannot be empty")
    if "/" in clean or "\\" in clean:
        raise ValueError("Domain cannot contain paths")
    if ":" in clean:
        raise ValueError("Domain cannot contain a port")
    if "@" in clean or "?" in clean or "#" in clean:
        raise ValueError("Domain contains invalid characters")

    # If full URL was somehow passed, extract hostname
    if clean.startswith(("http://", "https://")):
        host = urlsplit(clean).hostname
        if not host:
            raise ValueError(f"Invalid URL domain: {domain}")
        clean = host

    clean = clean.lower()
    clean = clean.removeprefix("www.")

    if "." not in clean:
        raise ValueError(f"Domain must contain a dot and valid TLD: {domain}")
    if not DOMAIN_REGEX.match(clean):
        raise ValueError(f"Invalid domain format: {domain}")

    return clean


def is_browser_app(app_id: str | None) -> bool:
    """Check if an app ID is a recognized web browser."""
    return bool(app_id and app_id.casefold() in BROWSER_APPS)


def extract_domain_from_title(title: str, app_id: str | None = None) -> str | None:
    """Attempt to detect website domain from a browser's window title.

    Handles titles like:
    - 'YouTube - Google Chrome' -> 'youtube.com'
    - 'Reddit - Dive into anything - Microsoft Edge' -> 'reddit.com'
    - 'docs.python.org - Google Chrome' -> 'python.org' or 'docs.python.org'
    """
    if not title:
        return None

    # Check known site titles first
    for needle, domain in KNOWN_SITE_TITLES:
        if needle in title:
            return domain

    # Look for raw domain embedded in title: e.g. "github.com - My Repo"
    match = re.search(r"\b([a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|org|net|io|dev|app|edu|gov|co|in|uk|de|ai|tech|me))\b", title, re.IGNORECASE)
    if match:
        try:
            return normalize_domain(match.group(1))
        except ValueError:
            pass

    return None
