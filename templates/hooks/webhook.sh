#!/bin/bash
# webhook.sh — Example generic webhook notification hook for spec-engine
# Usage: hook_on_task_complete="bash .claude/hooks/webhook.sh"
#
# Args vary by event:
#   wave_start:    spec_name, wave_number
#   task_complete: spec_name, task_id, status
#   spec_complete: spec_name, final_status
# Requires: WEBHOOK_URL environment variable

WEBHOOK="${WEBHOOK_URL:?Set WEBHOOK_URL to your webhook endpoint}"

# Send all arguments as JSON
payload="{\"event\": \"spec-engine\", \"args\": [$(printf '"%s",' "$@" | sed 's/,$//')]}"

curl -s -X POST "$WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "$payload" \
  > /dev/null 2>&1
