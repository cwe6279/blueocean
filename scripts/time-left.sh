#!/usr/bin/env bash
# Prints minutes remaining in the current session (from .session-deadline).
DEADLINE_FILE="$(dirname "$0")/../.session-deadline"
[ -f "$DEADLINE_FILE" ] || { echo "no session timer"; exit 0; }
left=$(( ($(cat "$DEADLINE_FILE") - $(date +%s)) / 60 ))
if [ "$left" -le 0 ]; then echo "TIME UP — wind down now"; else echo "$left minutes remaining"; fi
