#!/usr/bin/env bash
# spec-exec.sh — one iteration (one wave batch). Thin alias for spec-loop.sh --max-iterations 1.
exec "$(cd "$(dirname "$0")" && pwd)/spec-loop.sh" --max-iterations 1 "$@"
