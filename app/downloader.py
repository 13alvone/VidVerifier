#!/usr/bin/env python3

import os
import subprocess
import logging
import time
from typing import List
from app.utils import ascii_clean, sleep_random, is_url_downloaded, mark_url_downloaded

DB_PATH = os.path.join("app", "downloaded_links.db")
MAX_PLAYLIST_VIDS = int(os.getenv("MAX_PLAYLIST_VIDEOS", 20))

YT_DLP_BASE = [
    "yt-dlp",
    "--no-warnings",
    "--restrict-filenames",
    "--no-playlist",
    "--quiet",
    "--merge-output-format", "mp4",
    "-f", "bv*+ba/best[ext=mp4]",
    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
]

YT_DLP_FALLBACK = [
    "yt-dlp",
    "--quiet",
    "--merge-output-format", "mp4",
    "-f", "best",
    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
]

def _run_download(url: str, filename: str, attempt: int) -> bool:
	cmd = YT_DLP_BASE.copy()
	if attempt == 3:
		cmd = YT_DLP_FALLBACK.copy()

	cmd += ["-o", f"{filename}.mp4", url]
	logging.info(f"[i] Attempt {attempt}: {' '.join(cmd)}")
	try:
		subprocess.run(cmd, check=True)
		logging.info(f"[i] Downloaded: {filename}.mp4")
		return True
	except subprocess.CalledProcessError as e:
		logging.warning(f"[!] Attempt {attempt} failed: {e}")
		return False

def _attempt_with_retry(url: str, filename: str) -> bool:
	for attempt in range(1, 4):
		success = _run_download(url, filename, attempt)
		if success:
			return True
		if attempt < 3:
			backoff = 15 * attempt
			logging.info(f"[!] Backing off for {backoff}s before retrying...")
			time.sleep(backoff)
	return False

def download_videos(subject: str, urls: List[str]) -> List[str]:
	saved_files = []
	base = ascii_clean(subject)

	for idx, url in enumerate(urls):
		unique_id = url.strip().lower()
		if is_url_downloaded(DB_PATH, unique_id):
			logging.info(f"[i] Already downloaded: {url}")
			continue

		sleep_random()
		suffix = f"_{idx+1}" if len(urls) > 1 else ""
		fname = f"{base}{suffix}"

		if "playlist?list=" in url and "youtube.com" in url:
			logging.info(f"[i] Handling playlist: {url}")
			cmd = [
				"yt-dlp",
				"--flat-playlist",
				"--quiet",
				"--print", "url",
				"--playlist-end", str(MAX_PLAYLIST_VIDS),
				url
			]
			try:
				out = subprocess.check_output(cmd, text=True).strip().splitlines()
			except subprocess.CalledProcessError:
				logging.error(f"[x] Failed to extract playlist entries: {url}")
				continue

			for i, video_url in enumerate(out):
				playlist_suffix = f"{suffix}_{i+1}" if suffix else f"_{i+1}"
				video_fname = f"{base}{playlist_suffix}"
				if is_url_downloaded(DB_PATH, video_url):
					continue
				sleep_random()
				if _attempt_with_retry(video_url, video_fname):
					saved_files.append(f"{video_fname}.mp4")
					mark_url_downloaded(DB_PATH, video_url)

		else:
			if _attempt_with_retry(url, fname):
				saved_files.append(f"{fname}.mp4")
				mark_url_downloaded(DB_PATH, unique_id)

	return saved_files

