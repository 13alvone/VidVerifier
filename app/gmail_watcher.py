#!/usr/bin/env python3
"""
Gmail IMAP helper for VidVerifier.

Returns a list of tuples:
    (ascii_clean(subject), [url, …], factcheck_flag)
"""

from __future__ import annotations

import email
import imaplib
import logging
from email.header import decode_header
from typing import List, Tuple

from app.utils import ascii_clean, extract_urls

IMAP_SERVER = "imap.gmail.com"
MAILBOX = "INBOX"


# ─────────────────────────── helpers ────────────────────────────
def connect_gmail(username: str, app_password: str) -> imaplib.IMAP4_SSL:
    """Login and return an IMAP4_SSL instance."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(username, app_password)
    logging.info("[i] Gmail login successful")
    return mail


def _decode_subject(raw_subject) -> str:
    """
    Safely decode RFC 2047 headers.

    • Returns "(no subject)" if the header is missing or empty.
    • Falls back to UTF‑8 when the declared encoding is bogus.
    """
    if not raw_subject:
        return "(no subject)"
    try:
        subject, encoding = decode_header(raw_subject)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")
        return subject or "(no subject)"
    except Exception as exc:  # noqa: BLE001
        logging.debug(f"[!] Subject decode error: {exc!r}")
        return "(no subject)"


# ─────────────────────────── core API ────────────────────────────
def fetch_matching_emails(
    mail: imaplib.IMAP4_SSL,
    allowed_senders: List[str],
    search_criteria: str = "UNSEEN",
) -> List[Tuple[str, List[str], bool]]:
    """
    Retrieve messages that match `search_criteria` (IMAP syntax).

    Example criteria:
        "UNSEEN"                – unread only
        "ALL"                   – whole mailbox
        'SINCE "01-Jan-2024"'   – date range
    """
    mail.select(MAILBOX)
    status, data = mail.search(None, search_criteria)
    if status != "OK":
        raise RuntimeError(f"[x] IMAP search failed: {status}")

    message_nums = data[0].split()
    logging.info(f"[i] Found {len(message_nums)} messages for criteria '{search_criteria}'")

    results: List[Tuple[str, List[str], bool]] = []

    for num in message_nums:
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue

        msg = email.message_from_bytes(msg_data[0][1])
        from_addr = email.utils.parseaddr(msg.get("From"))[1].lower()

        if from_addr not in allowed_senders:
            continue

        subject = _decode_subject(msg.get("Subject"))
        factcheck = "factcheck" in subject.lower()

        # -------- extract plain‑text body ---------------------------------
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        urls = extract_urls(body)
        if urls:
            results.append((ascii_clean(subject), urls, factcheck))

    return results

