#!/usr/bin/env python3

import os
import logging
import whisper

MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
TRANSCRIPT_SUFFIX = ".txt"

model = whisper.load_model(MODEL_NAME)

def transcribe_videos(video_files):
	if not video_files:
		logging.info("[i] No videos to transcribe.")
		return

	for video in video_files:
		base, _ = os.path.splitext(video)
		out_txt = f"{base}{TRANSCRIPT_SUFFIX}"

		if os.path.exists(out_txt):
			logging.info(f"[i] Transcript exists: {out_txt}, skipping.")
			continue

		logging.info(f"[i] Transcribing: {video}")
		try:
			result = model.transcribe(video)
			with open(out_txt, "w", encoding="utf-8") as f:
				f.write(result["text"])
			logging.info(f"[i] Transcription saved: {out_txt}")
		except Exception as e:
			logging.error(f"[x] Transcription failed for {video}: {e}")

