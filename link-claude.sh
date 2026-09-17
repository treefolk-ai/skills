#!/bin/bash
#
# link-claude.sh — expose this repository's skills to Claude Code via symlinks.
#
# Targets: ~/.claude/skills    (regular claude sessions)
#          ~/.claude-ds/skills (claude-deepseek sessions, CLAUDE_CONFIG_DIR=~/.claude-ds)
#
# Idempotent: existing links/files are skipped. Source skill files are never modified.
# Run from anywhere; the repository root is derived from this script's location.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./link-claude.sh [--only claude|ds] [--unlink] [--dry-run]
       ./link-claude.sh --help

Symlink every skills/*/SKILL.md package into Claude Code's personal skill dirs.

Options:
  --only claude  Only target ~/.claude/skills
  --only ds      Only target ~/.claude-ds/skills
  --unlink       Remove symlinks that point into this repository (both targets
                 by default; combine with --only to remove one side only)
  --dry-run      Print actions without creating/removing anything
  --help, -h     Show this help message
EOF
}

# —— argument parsing ——
TARGETS=()
MODE=link
DRY=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --only)
      case "${2:-}" in
        claude) TARGETS=("$HOME/.claude/skills") ;;
        ds)     TARGETS=("$HOME/.claude-ds/skills") ;;
        *)      printf 'ERROR: --only requires claude or ds\n' >&2; exit 2 ;;
      esac
      shift 2 ;;
    --unlink)  MODE=unlink; shift ;;
    --dry-run) DRY=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'ERROR: unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
[ "${#TARGETS[@]}" -eq 0 ] && TARGETS=("$HOME/.claude/skills" "$HOME/.claude-ds/skills")

# —— repository root from this script's own location ——
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$script_dir
src="$repo_root/skills"

do_cmd() { if [ "$DRY" -eq 1 ]; then echo "[dry-run] $*"; else "$@"; fi; }

created=0 skipped=0 conflicts=0 removed=0

for side in "${TARGETS[@]}"; do
  case "$MODE" in
    link)
      do_cmd mkdir -p "$side"
      for d in "$src"/*/; do
        [ -f "$d/SKILL.md" ] || continue
        name=$(basename "$d")
        if [ -e "$side/$name" ] || [ -L "$side/$name" ]; then
          target=$(readlink "$side/$name" || true)
          if [ -L "$side/$name" ] && [ "${target%/}" = "${d%/}" ]; then
            skipped=$((skipped + 1))
          else
            echo "skip (name taken): $side/$name"
            conflicts=$((conflicts + 1))
          fi
          continue
        fi
        do_cmd ln -s "$d" "$side/$name"
        echo "link: $side/$name"
        created=$((created + 1))
      done
      ;;
    unlink)
      [ -d "$side" ] || continue
      for l in "$side"/*; do
        [ -L "$l" ] || continue
        case "$(readlink "$l")" in
          "$repo_root"/*)
            do_cmd rm "$l"
            echo "unlink: $l"
            removed=$((removed + 1)) ;;
        esac
      done
      ;;
  esac
done

echo "——"
if [ "$MODE" = link ]; then
  echo "linked $created, already linked $skipped, name conflicts $conflicts"
else
  echo "removed $removed"
fi
