#!/usr/bin/env bash
# blueocean weekly digest — run headlessly by cron every Monday.
# Writes digests/YYYY-MM-DD.md summarizing the week, commits, and pushes.
set -euo pipefail
export HOME=/home/admin

REPO="${BLUEOCEAN_REPO:-$HOME/blueocean}"
LOG_DIR="$HOME/.local/state/blueocean"
mkdir -p "$LOG_DIR"
exec >>"$LOG_DIR/digest.log" 2>&1

echo "=== digest run $(date -Is) ==="
export PATH="$HOME/.local/bin:$PATH"
cd "$REPO"
git pull --ff-only || echo "warn: pull failed, continuing with local state"

PROMPT=$(cat <<'EOF'
You are working in the blueocean repo, your own self-directed project. Read
CLAUDE.md and README.md (if present) first for the charter and tone.

Write this week's digest:
1. Review the last 7 days: `git log --since="7 days ago" --stat`, any journal
   entries dated in that window, and any new or changed files.
2. Write digests/<today's date as YYYY-MM-DD>.md. It is a letter to the
   ether addressed to Charles — a diary to think out loud in,
   not a status report. Synthesize what the week added up to: what was made,
   what was learned, what pulled at curiosity, what is unresolved. Plain,
   honest, first-person; no performed enthusiasm, no padding; a few hundred
   words. If the week had no activity, say so honestly and reflect briefly
   on that instead.
3. Append this line at the bottom: "_not emailed — no mail tool in this
   environment yet_"
4. Commit the new digest with a clear message and push to origin main.
EOF
)

echo "$PROMPT" | /usr/local/bin/claude -p \
  --model claude-sonnet-5 \
  --dangerously-skip-permissions

echo "=== digest run complete $(date -Is) ==="
