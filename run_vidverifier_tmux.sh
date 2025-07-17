#!/usr/bin/env bash
# run_vidverifier_tmux.sh — one‑shot launcher (no interactive attach)
#
#  • Starts/updates VidVerifier inside a detached tmux session.
#  • You can later inspect it with:   tmux attach -t vidverifier
#  • Stop everything with:            docker rm -f vidverifier ; tmux kill-session -t vidverifier
#
##############################################################################
# CONFIG — edit paths if needed
##############################################################################
SESSION="vidverifier"
WORK_DIR="/emby/emby_dataset/media/HOLDING/VidVerifier"
OUT_DIR="${WORK_DIR}/output"
ENV_FILE="${WORK_DIR}/.env"
LOG_FILE="${WORK_DIR}/tmux_launch.log"

##############################################################################
# safety checks
##############################################################################
set -euo pipefail
IFS=$'\n\t'

for cmd in tmux docker; do command -v "$cmd" >/dev/null || { echo "[x] $cmd missing"; exit 1; }; done
[[ -d  $WORK_DIR ]] || { echo "[x] WORK_DIR not found: $WORK_DIR"; exit 1; }
[[ -f  $ENV_FILE ]] || { echo "[x] .env missing: $ENV_FILE"; exit 1; }

##############################################################################
# prepare detached runner script
##############################################################################
RUNNER=$(mktemp /tmp/vv_runner.XXXX.sh)
chmod +x "$RUNNER"

cat >"$RUNNER" <<EOF
#!/usr/bin/env bash
set -e
echo "[i] Runner started — \$(date)"          | tee -a "$LOG_FILE"
cd "$WORK_DIR"

# ensure docker can read .env
chmod 644 "$ENV_FILE"

echo "[i] docker build…"                     | tee -a "$LOG_FILE"
docker build -t vidverifier:latest .        >>"$LOG_FILE" 2>&1

echo "[i] (re)starting container…"           | tee -a "$LOG_FILE"
docker container rm -f vidverifier >/dev/null 2>&1 || true
mkdir -p "$OUT_DIR"
docker run -d --name vidverifier --restart unless-stopped \
  -v "$OUT_DIR":/downloads \
  --env-file "$ENV_FILE" \
  -e GMAIL_SEARCH=ALL \
  vidverifier:latest                         >>"$LOG_FILE" 2>&1

echo "[✓] VidVerifier up — logs in tmux window 'logs'." | tee -a "$LOG_FILE"
EOF

##############################################################################
# create or replace tmux session (always detached)
##############################################################################
if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
fi

# window 0: build & run, then idle
tmux new-session  -d -s "$SESSION" -n run "bash '$RUNNER'; exec bash"

# window 1: live docker logs
tmux new-window   -t "$SESSION" -n logs \
     "bash -c 'echo \"[i] docker logs — Ctrl+C to stop pane\"; docker logs -f vidverifier'"

echo "[✓] VidVerifier tmux session '$SESSION' started."
echo "    • Attach anytime with:   tmux attach -t $SESSION"
echo "    • Stop with:             docker rm -f vidverifier && tmux kill-session -t $SESSION"

