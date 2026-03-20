#!/usr/bin/env bash
# lib/worktree.sh — Git worktree creation, reuse, and PR suggestion
# Source this file; do not execute directly.

# setup_worktree(spec_name, use_worktree)
# Creates or reuses a git worktree for isolated spec execution.
# Sets WORK_DIR to the worktree path (or pwd if use_worktree is false).
setup_worktree() {
  local spec_name="$1"
  local use_worktree="$2"

  if [[ "$use_worktree" != "true" ]]; then
    WORK_DIR="$(pwd)"
    return 0
  fi

  local worktree_base=".claude/specs/.worktrees"
  local worktree_path="$worktree_base/$spec_name"
  local branch_name="spec/$spec_name"

  # ensure .gitignore includes worktree dir
  if ! grep -qF '.claude/specs/.worktrees/' .gitignore 2>/dev/null; then
    echo '.claude/specs/.worktrees/' >> .gitignore
  fi

  mkdir -p "$worktree_base"

  if [[ -d "$worktree_path" ]]; then
    if [[ -f "$worktree_path/.git" ]]; then
      echo "Reusing existing worktree: $worktree_path"
    else
      echo "Stale worktree path found, recreating: $worktree_path"
      rm -rf "$worktree_path"
      git worktree prune
      _create_worktree "$worktree_path" "$branch_name"
    fi
  else
    git worktree prune
    _create_worktree "$worktree_path" "$branch_name"
  fi

  WORK_DIR="$(cd "$worktree_path" && pwd)"
}

# _create_worktree(path, branch)
_create_worktree() {
  local wt_path="$1"
  local branch="$2"

  if git show-ref --verify --quiet "refs/heads/$branch"; then
    git worktree add "$wt_path" "$branch"
  else
    git worktree add -b "$branch" "$wt_path"
  fi

  echo "Created worktree: $wt_path on branch $branch"
}

# print_pr_suggestion(spec_name)
print_pr_suggestion() {
  local spec_name="$1"
  echo ""
  echo "=== Next Steps ==="
  echo "  /spec-accept                          — Run user acceptance testing"
  echo "  /spec-docs                            — Generate documentation"
  echo "  gh pr create --head spec/$spec_name --title \"$spec_name\""
}
