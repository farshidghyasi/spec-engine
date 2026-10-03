#!/usr/bin/env bash
# spec-team.sh — team execution (Implementer + Tester + Reviewer + Debugger). Alias for spec-loop.sh --team.
exec "$(cd "$(dirname "$0")" && pwd)/spec-loop.sh" --team "$@"
