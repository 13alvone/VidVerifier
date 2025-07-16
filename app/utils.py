#!/usr/bin/env python3

import re
import time
import random
import logging
import sqlite3
import unicodedata
import os
from urllib.parse import urlparse, parse_qs, urlunparse

# ─────────────────────────────────────────────────────────────────────────────
# Robust URL Regex Patterns
# ─────────────────────────────────────────────────────────────────────────────

YOUTUBE_RE = re.compile(
    r'https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/|embed/|playlist\?list=)|youtu\.be/)[^\s]+',
    re.IGNORECASE
)

INSTAGRAM_RE = re.compile(
    r'https?://(?:www\.)?instagram\.com/(?:reel|p|tv|video)/[^\s/?]+',
    re.IGNORECASE
)

TIKTOK_RE = re.compile(
    r'https?://(?:www\.|m\.|vm\.)?tiktok\.com/[^ \n]+',
    re.IGNORECASE
)

VALID_URL_PATTERNS = [YOUTUBE_RE, INSTAGRAM_RE, TIKTOK_RE]

def extract_urls(text: str):
    urls = []
    for pattern in VALID_URL_PATTERNS:
        urls.extend(pattern.findall(text))

    # Clean up: strip query strings and whitespace
    cleaned = []
    for url in urls:
        parsed = urlparse(url.strip())
        clean_url = urlunparse(parsed._replace(query=""))
        cleaned.append(clean_url)

    return list(set(cleaned))

def ascii_clean(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "_", text.strip())
    return text[:100]

def sleep_random(min_sec=10, max_sec=30):
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

def mark_url_downloaded(db_path: str, url: str):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO downloads (url, timestamp) VALUES (?, strftime('%s','now'))", (url,))
        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        logging.error(f"[x] SQLite error (mark_url_downloaded): {e}")

