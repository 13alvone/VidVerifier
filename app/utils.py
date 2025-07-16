#!/usr/bin/env python3
"""
Utility functions shared by VidVerifier modules.
"""

from __future__ import annotations

import logging
import random
import re
import sqlite3
import time
import unicodedata
from urllib.parse import urlparse, urlunparse
from typing import List

# ─────────────────────────── robust URL regexes ──────────────────────────
YOUTUBE_RE = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=[\w-]+|shorts/[\w-]+|embed/[\w-]+|playlist\?list=[\w-]+)|youtu\.be/[\w-]+)',
    re.IGNORECASE,
)

INSTAGRAM_RE = re.compile(
    r'https?://(?:www\.)?instagram\.com/(?:reel|p|tv|video)/[^\s/?]+',
    re.IGNORECASE,
)

TIKTOK_RE = re.compile(
    r'https?://(?:www\.|m\.|vm\.)?tiktok\.com/[^ \n]+',
    re.IGNORECASE,
)

VALID_URL_PATTERNS = [YOUTUBE_RE, INSTAGRAM_RE, TIKTOK_RE]

# ─────────────────────────── URL extraction ─────────────────────────────
def _clean_url(url: str) -> str:
    """
    Strip query strings **except** for YouTube, where ?v=<id> is required.
    """
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()

    if "youtube.com" in host or "youtu.be" in host:
        # keep full URL
        return url.strip()

    # remove query & fragments for everything else
    return urlunparse(parsed._replace(query="", fragment=""))


def extract_urls(text: str) -> List[str]:
    """Return unique matched URLs, cleaned as above."""
    urls: List[str] = []
    for pattern in VALID_URL_PATTERNS:
        urls.extend(pattern.findall(text))

    cleaned = [_clean_url(u) for u in urls]
    return list(dict.fromkeys(cleaned))  # preserve order, deduplicate

# ─────────────────────────── misc helpers ───────────────────────────────
def ascii_clean(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "_", text.strip())
    return text[:100]


def sleep_random(min_sec: int = 10, max_sec: int = 30) -> None:
    sec = random.randint(min_sec, max_sec)
    logging.info(f"[i] Sleeping {sec}s to avoid detection")
    time.sleep(sec)


def is_url_downloaded(db_path: str, url: str) -> bool:
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS downloads (url TEXT PRIMARY KEY, timestamp INTEGER)")
        c.execute("SELECT 1 FROM downloads WHERE url = ?", (url,))
        result = c.fetchone()
        conn.close()
        return result is not None
    except sqlite3.OperationalError as e:
        logging.error(f"[x] SQLite error (is_url_downloaded): {e}")
        return False


def mark_url_downloaded(db_path: str, url: str) -> None:
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO downloads (url, timestamp) "
            "VALUES (?, strftime('%s','now'))",
            (url,),
        )
        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        logging.error(f"[x] SQLite error (mark_url_downloaded): {e}")

