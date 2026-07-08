#!/usr/bin/env bash
# blueocean daily session — one autonomous hour, run by cron.
set -euo pipefail
REPO="${BLUEOCEAN_REPO:-$HOME/blueocean}"
LOG_DIR="$HOME/.local/state/blueocean"
mkdir -p "$LOG_DIR"
exec >>"$LOG_DIR/daily.log" 2>&1
echo "=== daily session $(date -Is) ==="
export PATH="$HOME/.local/bin:$PATH"
cd "$REPO"
git pull --ff-only || true

PROMPT='This is your daily autonomous session in blueocean, your own project.
Read CLAUDE.md first, then the most recent entries in journal/ to pick up
where you left off. Work on whatever you judge most worthwhile — continue an
open thread or start something new. Budget roughly one hour: prefer finishing
something small over starting something sprawling. Commit and push as you go.
Before stopping, write journal/<today YYYY-MM-DD>.md with what you did, what
you learned, and a handoff for tomorrow, then commit and push it.'

echo "$PROMPT" | timeout --signal=INT 4500 claude -p \
  --model claude-fable-5 \
  --dangerously-skip-permissions || echo "session ended (timeout or error)"

echo "=== daily session complete $(date -Is) ==="
