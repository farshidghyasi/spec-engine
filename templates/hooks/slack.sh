#!/bin/bash
# slack.sh — Example Slack notification hook for spec-engine
# Usage: hook_on_spec_complete="bash .claude/hooks/slack.sh"
#
# Args: spec_name, final_status
# Requires: SLACK_WEBHOOK_URL environment variable

SPEC_NAME="${1:-unknown}"
STATUS="${2:-unknown}"

WEBHOOK="${SLACK_WEBHOOK_URL:?Set SLACK_WEBHOOK_URL to your Slack incoming webhook URL}"

curl -s -X POST "$WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "{\"text\": \"spec-engine: *${SPEC_NAME}* completed with status: ${STATUS}\"}" \
  > /dev/null 2>&1
