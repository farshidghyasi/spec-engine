#!/bin/bash
# discord.sh — Example Discord notification hook for spec-engine
# Usage: hook_on_spec_complete="bash .claude/hooks/discord.sh"
#
# Args: spec_name, final_status
# Requires: DISCORD_WEBHOOK_URL environment variable

SPEC_NAME="${1:-unknown}"
STATUS="${2:-unknown}"

WEBHOOK="${DISCORD_WEBHOOK_URL:?Set DISCORD_WEBHOOK_URL to your Discord webhook URL}"

curl -s -X POST "$WEBHOOK" \
  -H 'Content-Type: application/json' \
  -d "{\"content\": \"spec-engine: **${SPEC_NAME}** completed with status: ${STATUS}\"}" \
  > /dev/null 2>&1
