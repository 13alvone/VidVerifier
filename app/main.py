#!/usr/bin/env python3

import os
import logging
from dotenv import load_dotenv
from app import gmail_watcher, downloader, transcriber

# ─────────────────────────────────────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────────────────────────────────────
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
)

# ─────────────────────────────────────────────────────────────────────────────
# Environment & Config
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

EMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
raw_senders = os.getenv("ALLOWED_SENDERS", "")
ALLOWED_SENDERS = [s.strip().lower() for s in raw_senders.split(",") if s.strip()]

if not EMAIL_ADDRESS or not APP_PASSWORD:
	logging.error("[x] Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD in environment.")
        exit(1)

if not ALLOWED_SENDERS:
        logging.error("[x] No ALLOWED_SENDERS defined.")
        exit(1)

logging.info(f"[i] Using Gmail account: {EMAIL_ADDRESS}")
logging.info(f"[i] Allowed senders: {ALLOWED_SENDERS}")

# ─────────────────────────────────────────────────────────────────────────────
# Main Execution Loop
# ─────────────────────────────────────────────────────────────────────────────
def main():
	try:
		logging.info("[i] Connecting to Gmail...")
		mail = gmail_watcher.connect_gmail(EMAIL_ADDRESS, APP_PASSWORD)
		matching = gmail_watcher.fetch_matching_emails(mail, ALLOWED_SENDERS)

		if not matching:
			logging.info("[i] No matching emails found.")
			return

		for subject, urls, factcheck in matching:
			logging.info(f"[i] Processing: {subject}")
			saved = downloader.download_videos(subject, urls)
			if factcheck:
				transcriber.transcribe_videos(saved)

	except Exception as e:
		logging.error(f"[x] Unhandled error: {e}")
		exit(1)

if __name__ == "__main__":
	main()

