#!/usr/bin/env bash
# run_pipeline.sh - Entry point for FactCheck Pipeline Docker container

set -euo pipefail
IFS=$'\n\t'

LOG_PREFIX="[i]"

echo "${LOG_PREFIX} Starting FactCheck Pipeline..."

# Step 1: Activate virtual environment (if needed)
if [[ -f ".venv/bin/activate" ]]; then
	# shellcheck disable=SC1091
	source .venv/bin/activate
fi

# Step 2: Initialize DB if not exists
DB_PATH="/app/app/downloaded_links.db"
if [[ ! -f "$DB_PATH" ]]; then
	echo "${LOG_PREFIX} Initializing SQLite DB at $DB_PATH"
	python3 -c 'import sqlite3; sqlite3.connect("'"$DB_PATH"'").cursor().execute("CREATE TABLE IF NOT EXISTS downloads (url TEXT PRIMARY KEY, timestamp INTEGER)")'
fi

# Step 3: Run the pipeline
echo "${LOG_PREFIX} Launching main loop..."
export PYTHONPATH=/app
python3 -m app.main

