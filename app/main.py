#!/usr/bin/env python3
"""
VidVerifier – main orchestration loop.
"""

from __future__ import annotations
import logging, os, sys
from typing import List, Tuple
from dotenv import load_dotenv
from app import downloader, gmail_watcher, transcriber

# ── logging ───────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── env & validation ──────────────────────────────────────────────
load_dotenv()

EMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
APP_PASSWORD  = os.getenv("GMAIL_APP_PASSWORD")
ALLOWED_SENDERS = [s.strip().lower() for s in os.getenv("ALLOWED_SENDERS", "").split(",") if s.strip()]
SEARCH_CRITERIA = os.getenv("GMAIL_SEARCH", "UNSEEN")   # ← NEW

if not EMAIL_ADDRESS or not APP_PASSWORD:
    logging.error("[x] Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD.")
    sys.exit(1)
if not ALLOWED_SENDERS:
    logging.error("[x] No ALLOWED_SENDERS defined.")
    sys.exit(1)

logging.info(f"[i] Gmail account: {EMAIL_ADDRESS}")
logging.info(f"[i] Allowed senders: {ALLOWED_SENDERS}")
logging.info(f"[i] IMAP search criteria: {SEARCH_CRITERIA}")

# ── main ──────────────────────────────────────────────────────────
def run_pipeline() -> None:
    try:
        mail = gmail_watcher.connect_gmail(EMAIL_ADDRESS, APP_PASSWORD)
        matches: List[Tuple[str, List[str], bool]] = gmail_watcher.fetch_matching_emails(
            mail, ALLOWED_SENDERS, SEARCH_CRITERIA
        )

        if not matches:
            logging.info("[i] No matching emails found.")
            return

        for subject, urls, factcheck in matches:
            logging.info(f"[i] Processing: {subject}")
            saved = downloader.download_videos(subject, urls)
            if factcheck:
                transcriber.transcribe_videos(saved)

    except Exception as exc:          # noqa: BLE001
        logging.error(f"[x] Unhandled error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()

