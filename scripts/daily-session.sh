#!/usr/bin/env bash
# blueocean daily session — 45 autonomous minutes, run by cron.
set -euo pipefail
export HOME=/home/admin
REPO="${BLUEOCEAN_REPO:-$HOME/blueocean}"
LOG_DIR="$HOME/.local/state/blueocean"
mkdir -p "$LOG_DIR"
exec >>"$LOG_DIR/daily.log" 2>&1
echo "=== daily session $(date -Is) ==="
export PATH="/home/admin/.local/bin:/usr/local/bin:/usr/bin:/bin"
cd "$REPO"
git pull --ff-only || true

# start the session timer: 45 minutes from now
date -d '+45 minutes' +%s > "$REPO/.session-deadline"

PROMPT='This is your daily autonomous session in blueocean, your own project.
Read CLAUDE.md first, then the most recent entries in journal/ to pick up
where you left off.

A 45-minute session timer is running. Check it anytime by running:
  bash scripts/time-left.sh
Check it between tasks. When under ~10 minutes remain, stop starting new
work and wind down: finish or park what is in progress, commit and push,
and write journal/<today YYYY-MM-DD>.md with what you did, what you
learned, and a handoff for tomorrow. Never end with a dirty tree.

Work on whatever you judge most worthwhile — continue an open thread or
start something new. Prefer finishing something small over starting
something sprawling. Commit and push as you go.'

echo "$PROMPT" | timeout --signal=INT 3300 /usr/local/bin/claude -p \
  --model claude-fable-5 \
  --dangerously-skip-permissions || echo "session ended (timeout or error)"

rm -f "$REPO/.session-deadline"
echo "=== daily session complete $(date -Is) ==="
