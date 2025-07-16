#!/usr/bin/env bash
# test_all.sh - Test runner for FactCheck pipeline

set -euo pipefail
IFS=$'\n\t'

PYTHON=python3
LOG_PREFIX="[TEST]"

green() { echo -e "\033[1;32m$1\033[0m"; }
red()   { echo -e "\033[1;31m$1\033[0m"; }

echo "${LOG_PREFIX} Testing Gmail connectivity..."
if PYTHONPATH=. $PYTHON app/test_pipeline.py --gmail; then
	green "✓ Gmail connection and parsing successful"
else
	red "✗ Gmail connection test failed"
fi

echo "${LOG_PREFIX} Testing URL regex extraction..."
if PYTHONPATH=. $PYTHON app/test_pipeline.py --regex; then
	green "✓ Regex extraction successful"
else
	red "✗ Regex test failed"
fi

echo "${LOG_PREFIX} Testing download from sample URL..."
TEST_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
if PYTHONPATH=. $PYTHON app/test_pipeline.py --download "$TEST_URL"; then
	green "✓ Video download test successful"
else
	red "✗ Download test failed"
fi

echo "${LOG_PREFIX} Testing Whisper transcription..."
if ls test_subject*.mp4 >/dev/null 2>&1; then
	FILE=$(ls test_subject*.mp4 | head -n1)
	if PYTHONPATH=. $PYTHON app/test_pipeline.py --transcribe "$FILE"; then
		green "✓ Transcription test successful"
	else
		red "✗ Transcription test failed"
	fi
else
	red "✗ No MP4 file found to test transcription"
fi

