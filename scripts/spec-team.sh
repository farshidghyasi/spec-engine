#!/bin/bash
set -euo pipefail

# spec-team.sh — Thin CI/CD wrapper for /spec-team
# All business logic lives in skills/spec-team/SKILL.md
# This script only validates input and delegates to claude

SPEC_NAME=""
MAX_ITERATIONS=50

while [[ $# -gt 0 ]]; do
  case $1 in
    --spec-name) SPEC_NAME="$2"; shift 2 ;;
    --max-iterations) MAX_ITERATIONS="$2"; shift 2 ;;
    *) echo "Usage: spec-team.sh --spec-name <name> [--max-iterations N]"; exit 1 ;;
  esac
done

if [[ -z "$SPEC_NAME" ]]; then
  echo "Error: --spec-name is required"
  exit 1
fi

if [[ ! "$SPEC_NAME" =~ ^[a-z0-9][a-z0-9._-]{0,62}[a-z0-9]?$ ]]; then
  echo "Error: Invalid spec name. Use lowercase alphanumeric, hyphens, dots, underscores."
  exit 1
fi

if [[ ! -d ".claude/specs/$SPEC_NAME" ]]; then
  echo "Error: Spec not found: .claude/specs/$SPEC_NAME"
  exit 1
fi

claude -p "Run /spec-team for spec '$SPEC_NAME' with max iterations $MAX_ITERATIONS."
