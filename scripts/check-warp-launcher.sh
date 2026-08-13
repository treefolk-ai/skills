#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/check-warp-launcher.sh [--help]

Exercise the Warp `$push fast` launcher in private temporary repositories
without starting Codex or changing the caller's worktree.
EOF
}

if [ "$#" -gt 0 ]; then
  if [ "$#" -eq 1 ] && { [ "$1" = "--help" ] || [ "$1" = "-h" ]; }; then
    usage
    exit 0
  fi

  printf 'ERROR: unknown argument: %s\n' "$1" >&2
  usage >&2
  exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
launcher_file="$repo_root/push/adapters/warp/push-fast.yaml"

[ -f "$launcher_file" ] || {
  printf 'ERROR: launcher not found: %s\n' "$launcher_file" >&2
  exit 1
}

command_text=$(awk '
  $0 == "command: |-" {
    in_command = 1
    next
  }
  in_command && index($0, "  ") == 1 {
    if (line_count) {
      printf "\n"
    }
    printf "%s", substr($0, 3)
    line_count++
    next
  }
  in_command {
    exit
  }
  END {
    if (!line_count) {
      exit 1
    }
  }
' "$launcher_file") || {
  printf 'ERROR: launcher command is missing or malformed\n' >&2
  exit 1
}

temporary_base=${TMPDIR:-/tmp}
temporary_base=${temporary_base%/}
[ -n "$temporary_base" ] || temporary_base=/tmp
test_root=$(mktemp -d "$temporary_base/treefolk-warp-launcher.XXXXXX")
cleanup() {
  rm -rf -- "$test_root"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

fake_bin="$test_root/bin"
fake_codex="$fake_bin/codex"
git_repository="$test_root/repository"
outside_directory="$test_root/outside"
mkdir "$fake_bin" "$git_repository" "$outside_directory"

cat >"$fake_codex" <<'EOF'
#!/bin/sh
: "${TREEFOLK_WARP_CAPTURE:?}"
printf '%s\n' "$@" >"$TREEFOLK_WARP_CAPTURE"
EOF
chmod +x "$fake_codex"

git -C "$git_repository" init -q
git_repository=$(CDPATH= cd -P -- "$git_repository" && pwd)
mkdir "$git_repository/nested"
expected_arguments="$test_root/expected-arguments"
cat >"$expected_arguments" <<EOF
exec
--sandbox
workspace-write
-C
$git_repository
\$push fast
EOF

bash_path=$(command -v bash) || {
  printf 'ERROR: required test shell not found: bash\n' >&2
  exit 1
}
shell_paths=("$bash_path")
if zsh_path=$(command -v zsh 2>/dev/null); then
  shell_paths+=("$zsh_path")
fi

for shell_path in "${shell_paths[@]}"; do
  shell_name=${shell_path##*/}
  captured_arguments="$test_root/codex-arguments-$shell_name"

  if (
    cd "$outside_directory"
    PATH="$fake_bin:$PATH" TREEFOLK_WARP_CAPTURE="$captured_arguments" "$shell_path" -c "$command_text"
  ) >/dev/null 2>&1; then
    printf 'ERROR: launcher succeeded outside a Git repository under %s\n' "$shell_name" >&2
    exit 1
  fi

  [ ! -e "$captured_arguments" ] || {
    printf 'ERROR: launcher invoked Codex outside a Git repository under %s\n' "$shell_name" >&2
    exit 1
  }

  (
    cd "$git_repository/nested"
    PATH="$fake_bin:$PATH" TREEFOLK_WARP_CAPTURE="$captured_arguments" "$shell_path" -c "$command_text"
  )

  if ! cmp -s "$expected_arguments" "$captured_arguments"; then
    printf 'ERROR: launcher passed unexpected arguments to Codex under %s\n' "$shell_name" >&2
    diff -u "$expected_arguments" "$captured_arguments" >&2 || true
    exit 1
  fi
done

printf 'Warp launcher checks passed: non-repository stop, repository-root resolution, and exact Codex arguments.\n'
