#!/usr/bin/env python3
"""
Downloader module for VidVerifier.

Key points
──────────
• Unique filenames: <ascii_subject>_<urlhash>[optional_idx].mp4
  are written inside DOWNLOAD_DIR (defaults to /downloads).

• After download, SHA‑256 is checked:
      – new hash → file kept, hash stored
      – existing  → new file deleted, log notice

• If yt‑dlp exits 0 but produces no file, we retry / skip safely.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import List

from app.utils import (
    ascii_clean,
    is_url_downloaded,
    mark_url_downloaded,
    sleep_random,
)

DB_PATH = os.path.join("app", "downloaded_links.db")
MAX_PLAYLIST_VIDS = int(os.getenv("MAX_PLAYLIST_VIDEOS", 20))
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "/downloads"))

# yt‑dlp command templates -------------------------------------------------
YT_DLP_BASE = [
    "yt-dlp",
    "--no-warnings",
    "--restrict-filenames",
    "--no-playlist",
    "--quiet",
    "--merge-output-format",
    "mp4",
    "-f",
    "bv*+ba/best[ext=mp4]",
    "--user-agent",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "Chrome/114.0.0.0 Safari/537.36",
]

YT_DLP_FALLBACK = [
    "yt-dlp",
    "--quiet",
    "--merge-output-format",
    "mp4",
    "-f",
    "best",
    "--user-agent",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "Chrome/114.0.0.0 Safari/537.36",
]

# ─────────────────────────── DB helpers ────────────────────────────
def _ensure_hash_table() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS file_hashes ("
        "sha256 TEXT PRIMARY KEY, "
        "file_path TEXT NOT NULL)"
    )
    return conn


def _register_file(sha: str, path: Path) -> bool:
    """
    Insert (sha, path).  Return True if new; False if already present.
    """
    conn = _ensure_hash_table()
    try:
        with conn:
            conn.execute(
                "INSERT INTO file_hashes (sha256, file_path) VALUES (?, ?)",
                (sha, str(path)),
            )
        return True
    except sqlite3.IntegrityError:
        orig = conn.execute(
            "SELECT file_path FROM file_hashes WHERE sha256=?", (sha,)
        ).fetchone()
        logging.info(f"[i] Duplicate content detected → existing file: {orig[0]}")
        return False
    finally:
        conn.close()

# ─────────────────────────── misc helpers ─────────────────────────
def _url_hash(url: str, length: int = 8) -> str:
    return hashlib.sha256(url.encode(), usedforsecurity=False).hexdigest()[:length]


def _safe_filename(subject: str, url: str, suffix: str = "") -> Path:
    """
    Build an *absolute* path in DOWNLOAD_DIR with a unique, ascii‑safe name.
    """
    base = ascii_clean(subject)
    fname = f"{base}_{_url_hash(url)}{suffix}.mp4"
    return DOWNLOAD_DIR / fname


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

# ─────────────── download w/ verification & retries ───────────────
def _run_download(url: str, target: Path, attempt: int) -> bool:
    cmd = YT_DLP_FALLBACK.copy() if attempt == 3 else YT_DLP_BASE.copy()
    cmd += ["-o", str(target), url]
    logging.info(f"[i] Attempt {attempt}: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        logging.warning(f"[!] Attempt {attempt} failed (yt‑dlp error): {exc}")
        return False

    if target.exists():
        logging.info(f"[i] Downloaded: {target.name}")
        return True

    logging.warning(f"[!] Attempt {attempt} produced no file (url='{url}')")
    return False


def _attempt_with_retry(url: str, target: Path) -> bool:
    for attempt in range(1, 4):
        if _run_download(url, target, attempt):
            return True
        if attempt < 3:
            backoff = 15 * attempt
            logging.info(f"[!] Backing off for {backoff}s before retrying…")
            time.sleep(backoff)
    return False

# ───────────────────────── public API ─────────────────────────────
def download_videos(subject: str, urls: List[str]) -> List[str]:
    saved_files: List[str] = []
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    for idx, url in enumerate(urls):
        uid = url.strip().lower()
        if is_url_downloaded(DB_PATH, uid):
            logging.info(f"[i] Already downloaded: {url}")
            continue

        sleep_random()
        ord_suffix = f"_{idx+1}" if len(urls) > 1 else ""
        target = _safe_filename(subject, url, ord_suffix)

        if "playlist?list=" in url and "youtube.com" in url:
            _handle_playlist(url, subject, ord_suffix, saved_files)
            continue

        if _attempt_with_retry(url, target):
            sha = _file_sha256(target)
            if _register_file(sha, target):
                saved_files.append(str(target))
            else:
                target.unlink(missing_ok=True)
            mark_url_downloaded(DB_PATH, uid)

    return saved_files

# ───────────────────── playlist support (unchanged) ───────────────
def _handle_playlist(url: str, subject: str, suffix: str, saved_files: List[str]):
    logging.info(f"[i] Handling playlist: {url}")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--quiet",
        "--print",
        "url",
        "--playlist-end",
        str(MAX_PLAYLIST_VIDS),
        url,
    ]
    try:
        entries = subprocess.check_output(cmd, text=True).strip().splitlines()
    except subprocess.CalledProcessError:
        logging.error(f"[x] Failed to extract playlist entries: {url}")
        return

    for i, video_url in enumerate(entries):
        if is_url_downloaded(DB_PATH, video_url):
            continue
        sleep_random()
        psuffix = f"{suffix}_{i+1}" if suffix else f"_{i+1}"
        target = _safe_filename(subject, video_url, psuffix)

        if _attempt_with_retry(video_url, target):
            sha = _file_sha256(target)
            if _register_file(sha, target):
                saved_files.append(str(target))
            else:
                target.unlink(missing_ok=True)
            mark_url_downloaded(DB_PATH, video_url)

