#!/usr/bin/env bash
# run_pipeline.sh – Entry point inside the Docker container

set -euo pipefail
IFS=$'\n\t'

LOG_PREFIX="[i]"

echo "${LOG_PREFIX} Starting FactCheck Pipeline..."

# Activate venv if present
[[ -f ".venv/bin/activate" ]] && source .venv/bin/activate

# Ensure DB exists
DB_PATH="/app/app/downloaded_links.db"
if [[ ! -f "$DB_PATH" ]]; then
  echo "${LOG_PREFIX} Initializing SQLite DB at $DB_PATH"
  python3 - <<PY
import sqlite3, sys, pathlib
db = pathlib.Path("$DB_PATH")
db.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(db)
conn.execute("CREATE TABLE IF NOT EXISTS downloads (url TEXT PRIMARY KEY, timestamp INTEGER)")
conn.execute("CREATE TABLE IF NOT EXISTS file_hashes (sha256 TEXT PRIMARY KEY, file_path TEXT)")
conn.close()
PY
fi

# Ensure download directory exists
mkdir -p /downloads

# Run main loop
echo "${LOG_PREFIX} Launching main loop..."
export PYTHONPATH=/app
python3 -m app.main

