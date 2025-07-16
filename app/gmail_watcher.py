#!/usr/bin/env python3

import imaplib
import email
import re
from email.header import decode_header
from typing import List, Tuple
from app.utils import extract_urls, ascii_clean

IMAP_SERVER = "imap.gmail.com"
MAILBOX = "INBOX"

def connect_gmail(username: str, app_password: str):
	try:
		mail = imaplib.IMAP4_SSL(IMAP_SERVER)
		mail.login(username, app_password)
		return mail
	except imaplib.IMAP4.error as e:
		raise RuntimeError(f"[x] Gmail login failed: {e}")

def fetch_matching_emails(mail, allowed_senders: List[str]) -> List[Tuple[str, List[str], bool]]:
	mail.select(MAILBOX)
	status, data = mail.search(None, "UNSEEN")
	if status != "OK":
		raise RuntimeError("[x] Unable to search mailbox.")

	results = []
	for num in data[0].split():
		status, msg_data = mail.fetch(num, "(RFC822)")
		if status != "OK":
			continue

		msg = email.message_from_bytes(msg_data[0][1])
		from_field = email.utils.parseaddr(msg.get("From"))[1].lower()

		if from_field not in allowed_senders:
			continue

		subject, encoding = decode_header(msg["Subject"])[0]
		if isinstance(subject, bytes):
			subject = subject.decode(encoding or "utf-8", errors="ignore")

		factcheck = "factcheck" in subject.lower()

		# Extract body
		body = ""
		if msg.is_multipart():
			for part in msg.walk():
				content_type = part.get_content_type()
				if content_type == "text/plain":
					body = part.get_payload(decode=True).decode(errors="ignore")
					break
		else:
			body = msg.get_payload(decode=True).decode(errors="ignore")

		urls = extract_urls(body)
		if urls:
			results.append((ascii_clean(subject), urls, factcheck))

	return results

