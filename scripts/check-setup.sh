#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/check-setup.sh [--help]

Exercise setup, migration, and uninstall behavior in private temporary targets.
EOF
}

if [ "$#" -gt 0 ]; then
  if [ "$#" -eq 1 ] && { [ "$1" = --help ] || [ "$1" = -h ]; }; then
    usage
    exit 0
  fi

  printf 'check-setup: unknown argument: %s\n' "$1" >&2
  usage >&2
  exit 2
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
setup_script="$repo_root/setup"
uninstall_script="$repo_root/uninstall"

[ -x "$setup_script" ] || {
  printf 'check-setup: setup is not executable: %s\n' "$setup_script" >&2
  exit 1
}
[ -x "$uninstall_script" ] || {
  printf 'check-setup: uninstall is not executable: %s\n' "$uninstall_script" >&2
  exit 1
}

export LC_ALL=C

temporary_base=${TMPDIR:-/tmp}
temporary_base=${temporary_base%/}
[ -n "$temporary_base" ] || temporary_base=/tmp
test_root=

cleanup() {
  if [ -n "$test_root" ] && [ -d "$test_root" ]; then
    case "$test_root" in
      "$temporary_base"/treefolk-check-setup.*)
        rm -rf -- "$test_root"
        ;;
      *)
        printf 'check-setup: refusing to clean unexpected path: %s\n' "$test_root" >&2
        ;;
    esac
  fi
}

trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

test_root=$(mktemp -d "$temporary_base/treefolk-check-setup.XXXXXX") || {
  printf 'check-setup: could not create temporary directory\n' >&2
  exit 1
}
test_home="$test_root/home"
mkdir "$test_home"

check_count=0
command_status=0

fail() {
  local message=$1
  local output_file=${2:-}

  printf 'FAIL: %s\n' "$message" >&2
  if [ -n "$output_file" ] && [ -f "$output_file" ]; then
    printf '%s\n' '--- command output ---' >&2
    sed 's/^/  /' "$output_file" >&2
  fi
  exit 1
}

pass() {
  check_count=$((check_count + 1))
}

require_temporary_target() {
  case "$1" in
    "$test_root"/*) ;;
    *) fail "internal error: target is outside the temporary root: $1" ;;
  esac
}

run_setup() {
  local output_file=$1
  local target=$2
  shift 2

  require_temporary_target "$target"
  set +e
  TREEFOLK_SKILLS_DIR="$target" HOME="$test_home" \
    "$setup_script" "$@" >"$output_file" 2>&1
  command_status=$?
  set -e
}

run_uninstall() {
  local output_file=$1
  local target=$2
  shift 2

  require_temporary_target "$target"
  set +e
  TREEFOLK_SKILLS_DIR="$target" HOME="$test_home" \
    "$uninstall_script" "$@" >"$output_file" 2>&1
  command_status=$?
  set -e
}

assert_status() {
  local expected=$1
  local label=$2
  local output_file=$3

  [ "$command_status" -eq "$expected" ] ||
    fail "$label: expected exit $expected, got $command_status" "$output_file"
  pass
}

assert_output_contains() {
  local output_file=$1
  local expected=$2
  local label=$3

  grep -F "$expected" "$output_file" >/dev/null 2>&1 ||
    fail "$label: missing output: $expected" "$output_file"
  pass
}

assert_absent() {
  local path=$1
  local label=$2

  if [ -e "$path" ] || [ -L "$path" ]; then
    fail "$label: expected no filesystem entry at $path"
  fi
  pass
}

assert_raw_link() {
  local path=$1
  local expected=$2
  local label=$3
  local raw_output actual

  [ -L "$path" ] || fail "$label: expected a symlink at $path"
  raw_output=$(readlink -n "$path" && printf '.') ||
    fail "$label: could not read symlink at $path"
  actual=${raw_output%.}
  [ "$actual" = "$expected" ] ||
    fail "$label: expected link target $expected, got $actual"
  pass
}

assert_link_resolves_to() {
  local path=$1
  local expected=$2
  local label=$3
  local actual_physical
  local expected_physical

  [ -L "$path" ] || fail "$label: expected a symlink at $path"
  actual_physical=$(CDPATH= cd -P "$path" 2>/dev/null && pwd) ||
    fail "$label: symlink does not resolve to a directory: $path"
  expected_physical=$(CDPATH= cd -P "$expected" 2>/dev/null && pwd) ||
    fail "$label: expected directory is unavailable: $expected"
  [ "$actual_physical" = "$expected_physical" ] ||
    fail "$label: expected $expected_physical, got $actual_physical"
  pass
}

expect_setup_exit_2() {
  local label=$1
  local expected_message=$2
  shift 2
  local output_file="$test_root/output-$label.txt"
  local target="$test_root/arguments-target"

  run_setup "$output_file" "$target" "$@"
  assert_status 2 "$label" "$output_file"
  assert_output_contains "$output_file" "$expected_message" "$label"
}

current_names=()
legacy_names=(commit-push c-push setup-repo s-repo)

shopt -s nullglob
for current_skill_file in "$repo_root"/*/SKILL.md; do
  current_skill_dir=${current_skill_file%/SKILL.md}
  current_names[${#current_names[@]}]=${current_skill_dir##*/}
done
shopt -u nullglob
[ "${#current_names[@]}" -gt 0 ] || fail 'no top-level skills are available to test'

for migration_replacement in repo push; do
  [ -f "$repo_root/$migration_replacement/SKILL.md" ] ||
    fail "required migration replacement is unavailable: $migration_replacement"
done

# The host defaults to Codex, while both supported explicit syntaxes remain valid.
default_target="$test_root/default-target"
default_output="$test_root/output-default.txt"
run_setup "$default_output" "$default_target" --dry-run
assert_status 0 'default host' "$default_output"
assert_output_contains "$default_output" 'Host: codex' 'default host'
assert_output_contains "$default_output" 'Mode: dry-run' 'default host'
assert_absent "$default_target" 'default host dry-run'

explicit_target="$test_root/explicit-target"
explicit_output="$test_root/output-explicit.txt"
run_setup "$explicit_output" "$explicit_target" --host codex --dry-run
assert_status 0 'explicit separated host' "$explicit_output"
assert_output_contains "$explicit_output" 'Host: codex' 'explicit separated host'
assert_absent "$explicit_target" 'explicit separated host dry-run'

equals_target="$test_root/equals-target"
equals_output="$test_root/output-equals.txt"
run_setup "$equals_output" "$equals_target" --host=codex --dry-run
assert_status 0 'explicit equals host' "$equals_output"
assert_output_contains "$equals_output" 'Host: codex' 'explicit equals host'
assert_absent "$equals_target" 'explicit equals host dry-run'

# Parser failures must be usage errors, including every duplicate-host spelling.
expect_setup_exit_2 missing-host-value 'setup: --host requires a value' --host
expect_setup_exit_2 empty-host-equals 'setup: unsupported host:  (expected codex)' --host=
expect_setup_exit_2 empty-host-separated 'setup: unsupported host:  (expected codex)' --host ''
expect_setup_exit_2 unsupported-host 'setup: unsupported host: claude (expected codex)' --host claude
expect_setup_exit_2 duplicate-host-separated 'setup: --host may be specified only once' --host codex --host codex
expect_setup_exit_2 duplicate-host-equals 'setup: --host may be specified only once' --host=codex --host=codex
expect_setup_exit_2 duplicate-host-mixed-a 'setup: --host may be specified only once' --host codex --host=codex
expect_setup_exit_2 duplicate-host-mixed-b 'setup: --host may be specified only once' --host=codex --host codex
assert_absent "$test_root/arguments-target" 'argument failures'

# Seed all historical names exactly as older setup versions installed them.
upgrade_target="$test_root/upgrade-target"
mkdir "$upgrade_target"
for legacy_name in "${legacy_names[@]}"; do
  ln -s "$repo_root/$legacy_name" "$upgrade_target/$legacy_name"
done

# A migration dry-run may report removals, but it must not alter any link.
upgrade_dry_output="$test_root/output-upgrade-dry-run.txt"
run_setup "$upgrade_dry_output" "$upgrade_target" --dry-run
assert_status 0 'legacy migration dry-run' "$upgrade_dry_output"
for legacy_name in "${legacy_names[@]}"; do
  assert_raw_link \
    "$upgrade_target/$legacy_name" \
    "$repo_root/$legacy_name" \
    "legacy migration dry-run ($legacy_name)"
done
for current_name in "${current_names[@]}"; do
  assert_absent \
    "$upgrade_target/$current_name" \
    "legacy migration dry-run ($current_name)"
done

# A real setup removes only verified historical links and activates current names.
upgrade_output="$test_root/output-upgrade.txt"
run_setup "$upgrade_output" "$upgrade_target"
assert_status 0 'legacy migration' "$upgrade_output"
for legacy_name in "${legacy_names[@]}"; do
  assert_absent "$upgrade_target/$legacy_name" "legacy migration ($legacy_name)"
done
for current_name in "${current_names[@]}"; do
  assert_link_resolves_to \
    "$upgrade_target/$current_name" \
    "$repo_root/$current_name" \
    "current activation ($current_name)"
done

# Uninstall removes the links created for the current public surface.
uninstall_output="$test_root/output-uninstall.txt"
run_uninstall "$uninstall_output" "$upgrade_target" --host codex
assert_status 0 'uninstall current links' "$uninstall_output"
for current_name in "${current_names[@]}"; do
  assert_absent "$upgrade_target/$current_name" "uninstall ($current_name)"
done

# Direct uninstall must also clean up owned historical links even when the new
# setup has never had a chance to migrate them.
direct_uninstall_target="$test_root/direct-uninstall-target"
mkdir "$direct_uninstall_target"
for legacy_name in "${legacy_names[@]}"; do
  ln -s "$repo_root/$legacy_name" "$direct_uninstall_target/$legacy_name"
done

direct_uninstall_dry_output="$test_root/output-direct-uninstall-dry-run.txt"
run_uninstall \
  "$direct_uninstall_dry_output" \
  "$direct_uninstall_target" \
  --host codex \
  --dry-run
assert_status 0 'direct legacy uninstall dry-run' "$direct_uninstall_dry_output"
for legacy_name in "${legacy_names[@]}"; do
  assert_output_contains \
    "$direct_uninstall_dry_output" \
    "remove    $legacy_name (owned legacy link" \
    "direct legacy uninstall dry-run ($legacy_name)"
  assert_raw_link \
    "$direct_uninstall_target/$legacy_name" \
    "$repo_root/$legacy_name" \
    "direct legacy uninstall dry-run ($legacy_name)"
done

direct_uninstall_output="$test_root/output-direct-uninstall.txt"
run_uninstall "$direct_uninstall_output" "$direct_uninstall_target" --host codex
assert_status 0 'direct legacy uninstall' "$direct_uninstall_output"
for legacy_name in "${legacy_names[@]}"; do
  assert_absent \
    "$direct_uninstall_target/$legacy_name" \
    "direct legacy uninstall ($legacy_name)"
done

# A same-named link owned by somebody else must never be treated as legacy state.
safety_target="$test_root/safety-target"
unrelated_dir="$test_root/unrelated/c-push"
mkdir -p "$safety_target" "$unrelated_dir"
ln -s "$unrelated_dir" "$safety_target/c-push"
newline_legacy_target="$repo_root/s-repo"$'\n'
ln -s "$newline_legacy_target" "$safety_target/s-repo"

safety_output="$test_root/output-safety.txt"
run_setup "$safety_output" "$safety_target"
assert_status 0 'unrelated legacy-named link' "$safety_output"
assert_raw_link \
  "$safety_target/c-push" \
  "$unrelated_dir" \
  'unrelated legacy-named link'
assert_raw_link \
  "$safety_target/s-repo" \
  "$newline_legacy_target" \
  'newline-suffixed legacy-named link'
for current_name in "${current_names[@]}"; do
  assert_link_resolves_to \
    "$safety_target/$current_name" \
    "$repo_root/$current_name" \
    "safety activation ($current_name)"
done

safety_uninstall_output="$test_root/output-safety-uninstall.txt"
run_uninstall "$safety_uninstall_output" "$safety_target" --host codex
assert_status 0 'safety-target uninstall' "$safety_uninstall_output"
assert_raw_link \
  "$safety_target/c-push" \
  "$unrelated_dir" \
  'unrelated link after uninstall'
assert_raw_link \
  "$safety_target/s-repo" \
  "$newline_legacy_target" \
  'newline-suffixed link after uninstall'
for current_name in "${current_names[@]}"; do
  assert_absent "$safety_target/$current_name" "safety-target uninstall ($current_name)"
done

printf 'PASS: setup regression checks completed (%d assertions).\n' "$check_count"
