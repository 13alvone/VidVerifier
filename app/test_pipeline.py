#!/usr/bin/env python3

import argparse
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import gmail_watcher, utils, transcriber, downloader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

# Ensure DB exists for downloader test
DB_PATH = os.path.join("app", "downloaded_links.db")
if not os.path.exists(DB_PATH):
	from sqlite3 import connect
	conn = connect(DB_PATH)
	conn.execute("CREATE TABLE IF NOT EXISTS downloads (url TEXT PRIMARY KEY, timestamp INTEGER)")
	conn.commit()
	conn.close()

parser = argparse.ArgumentParser(description="Test FactCheck Pipeline Components")
parser.add_argument("--gmail", action="store_true", help="Test Gmail connection and email parsing")
parser.add_argument("--regex", action="store_true", help="Test regex-based URL extraction")
parser.add_argument("--download", metavar="URL", help="Test yt-dlp download logic with sample URL")
parser.add_argument("--transcribe", metavar="MP4", help="Test Whisper transcription on an MP4 file")
args = parser.parse_args()

email = os.getenv("GMAIL_ADDRESS")
password = os.getenv("GMAIL_APP_PASSWORD")
allowed_senders = os.getenv("ALLOWED_SENDERS", "").lower().split(",")

if args.gmail:
	if not email or not password:
		logging.error("[x] GMAIL_ADDRESS or GMAIL_APP_PASSWORD is missing in .env")
	else:
		logging.info("[i] Connecting to Gmail...")
		mail = gmail_watcher.connect_gmail(email, password)
		emails = gmail_watcher.fetch_matching_emails(mail, allowed_senders)
		for subj, urls, factcheck in emails:
			print(f"\nSubject: {subj}\nFactcheck: {factcheck}\nURLs: {urls}")

if args.regex:
	sample_text = """
		Check these out:
		https://www.youtube.com/watch?v=dQw4w9WgXcQ
		https://www.tiktok.com/@someone/video/123456
		https://instagram.com/reel/abcxyz
	"""
	urls = utils.extract_urls(sample_text)
	print(f"[i] Found URLs: {urls}")

if args.download:
	saved = downloader.download_videos("test_subject", [args.download])
	print(f"[i] Downloaded files: {saved}")

if args.transcribe:
	transcriber.transcribe_videos([args.transcribe])

