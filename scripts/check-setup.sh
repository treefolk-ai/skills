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

# Older installers recorded physical source paths. Match setup's path handling
# even when this checkout is reached through /var -> /private/var or another
# directory symlink, so the legacy links below represent real owned installs.
script_dir=$(CDPATH= cd -P -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -P -- "$script_dir/.." && pwd)
package_root="$repo_root/skills"
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
  (
    unset CODEX_HOME
    TREEFOLK_SKILLS_DIR="$target" HOME="$test_home" \
      "$setup_script" "$@"
  ) >"$output_file" 2>&1
  command_status=$?
  set -e
}

run_uninstall() {
  local output_file=$1
  local target=$2
  shift 2

  require_temporary_target "$target"
  set +e
  (
    unset CODEX_HOME
    TREEFOLK_SKILLS_DIR="$target" HOME="$test_home" \
      "$uninstall_script" "$@"
  ) >"$output_file" 2>&1
  command_status=$?
  set -e
}

run_default_setup() {
  local output_file=$1
  shift

  set +e
  (
    unset TREEFOLK_SKILLS_DIR CODEX_HOME
    HOME="$test_home" "$setup_script" "$@"
  ) >"$output_file" 2>&1
  command_status=$?
  set -e
}

run_default_uninstall() {
  local output_file=$1
  shift

  set +e
  (
    unset TREEFOLK_SKILLS_DIR CODEX_HOME
    HOME="$test_home" "$uninstall_script" "$@"
  ) >"$output_file" 2>&1
  command_status=$?
  set -e
}

# Alternate checkouts and homes remain wholly inside this test's temporary root.
# Never inherit the caller's activation overrides into a filesystem test.
run_in_private_home() {
  local output_file=$1
  local isolated_home=$2
  shift 2

  require_temporary_target "$isolated_home"
  set +e
  (
    unset TREEFOLK_SKILLS_DIR CODEX_HOME
    HOME="$isolated_home" "$@"
  ) >"$output_file" 2>&1
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
for current_skill_file in "$package_root"/*/SKILL.md; do
  current_skill_dir=${current_skill_file%/SKILL.md}
  current_names[${#current_names[@]}]=${current_skill_dir##*/}
done
shopt -u nullglob
[ "${#current_names[@]}" -gt 0 ] || fail 'no packages in skills/ are available to test'

for migration_replacement in repo push; do
  [ -f "$package_root/$migration_replacement/SKILL.md" ] ||
    fail "required migration replacement is unavailable: $migration_replacement"
done

# The host defaults to Codex for compatibility, while Codex and Grok both use
# the same shared activation behavior.
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

grok_target="$test_root/grok-target"
grok_output="$test_root/output-grok.txt"
run_setup "$grok_output" "$grok_target" --host grok --dry-run
assert_status 0 'explicit Grok host' "$grok_output"
assert_output_contains "$grok_output" 'Host: grok' 'explicit Grok host'
assert_absent "$grok_target" 'explicit Grok host dry-run'

# Parser failures must be usage errors, including every duplicate-host spelling.
expect_setup_exit_2 missing-host-value 'setup: --host requires a value' --host
expect_setup_exit_2 empty-host-equals 'setup: unsupported host:  (expected codex or grok)' --host=
expect_setup_exit_2 empty-host-separated 'setup: unsupported host:  (expected codex or grok)' --host ''
expect_setup_exit_2 unsupported-host 'setup: unsupported host: claude (expected codex or grok)' --host claude
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
    "$package_root/$current_name" \
    "current activation ($current_name)"
done

# Uninstall removes the links created for the current public surface.
uninstall_output="$test_root/output-uninstall.txt"
run_uninstall "$uninstall_output" "$upgrade_target" --host codex
assert_status 0 'uninstall current links' "$uninstall_output"
for current_name in "${current_names[@]}"; do
  assert_absent "$upgrade_target/$current_name" "uninstall ($current_name)"
done

# Moving the package directory does not rename the public skill. An existing
# exact old source link may be dangling after an upgrade, but is still owned.
layout_target="$test_root/layout-target"
mkdir "$layout_target"
for current_name in "${current_names[@]}"; do
  ln -s "$repo_root/$current_name" "$layout_target/$current_name"
done

layout_dry_output="$test_root/output-layout-dry.txt"
run_setup "$layout_dry_output" "$layout_target" --dry-run
assert_status 0 'same-name layout migration dry-run' "$layout_dry_output"
for current_name in "${current_names[@]}"; do
  assert_raw_link "$layout_target/$current_name" "$repo_root/$current_name" \
    "same-name migration dry-run ($current_name)"
done

layout_output="$test_root/output-layout.txt"
run_setup "$layout_output" "$layout_target"
assert_status 0 'same-name layout migration' "$layout_output"
for current_name in "${current_names[@]}"; do
  assert_link_resolves_to "$layout_target/$current_name" "$package_root/$current_name" \
    "same-name migration ($current_name)"
done

layout_repeat_output="$test_root/output-layout-repeat.txt"
run_setup "$layout_repeat_output" "$layout_target"
assert_status 0 'same-name migration repeated' "$layout_repeat_output"
assert_output_contains "$layout_repeat_output" 'Installed: 0' 'layout migration idempotence'
assert_output_contains "$layout_repeat_output" 'Migrated: 0' 'layout migration idempotence'
for current_name in "${current_names[@]}"; do
  assert_link_resolves_to "$layout_target/$current_name" "$package_root/$current_name" \
    "same-name repeat ($current_name)"
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
    "$package_root/$current_name" \
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

# Every shared-target conflict is found before any old links are migrated,
# including links in the compatibility directory. Lookalike paths are not proof
# of ownership, and a real same-named directory is never a replaceable link.
for conflict_kind in external directory newline; do
  conflict_home="$test_root/conflict-home-$conflict_kind"
  conflict_shared="$conflict_home/.agents/skills"
  conflict_legacy="$conflict_home/.codex/skills"
  mkdir -p "$conflict_shared" "$conflict_legacy"
  ln -s "$repo_root/geo" "$conflict_shared/geo"
  ln -s "$repo_root/geo" "$conflict_legacy/geo"
  ln -s "$repo_root/c-push" "$conflict_shared/c-push"
  case "$conflict_kind" in
    external)
      conflict_source="$test_root/external-push"
      mkdir "$conflict_source"
      ln -s "$conflict_source" "$conflict_shared/push"
      ;;
    directory)
      mkdir "$conflict_shared/push"
      printf '%s\n' 'user-owned content' >"$conflict_shared/push/keep.txt"
      ;;
    newline)
      conflict_source="$repo_root/push"$'\n'
      ln -s "$conflict_source" "$conflict_shared/push"
      ;;
  esac
  for conflict_mode in dry real; do
    conflict_output="$test_root/output-conflict-$conflict_kind-$conflict_mode.txt"
    if [ "$conflict_mode" = dry ]; then
      run_in_private_home "$conflict_output" "$conflict_home" "$setup_script" --dry-run
    else
      run_in_private_home "$conflict_output" "$conflict_home" "$setup_script"
    fi
    assert_status 1 "shared conflict ($conflict_kind, $conflict_mode)" "$conflict_output"
    assert_raw_link "$conflict_shared/geo" "$repo_root/geo" 'shared migration blocked by conflict'
    assert_raw_link "$conflict_legacy/geo" "$repo_root/geo" 'legacy migration blocked by shared conflict'
    assert_raw_link "$conflict_shared/c-push" "$repo_root/c-push" 'alias removal blocked by conflict'
    assert_absent "$conflict_shared/repo" 'no partial activation on conflict'
    if [ "$conflict_kind" = directory ]; then
      [ -d "$conflict_shared/push" ] && [ ! -L "$conflict_shared/push" ] ||
        fail 'conflict directory was replaced'
      [ "$(cat "$conflict_shared/push/keep.txt")" = 'user-owned content' ] ||
        fail 'conflict directory contents changed'
      pass
    else
      assert_raw_link "$conflict_shared/push" "$conflict_source" 'conflicting link preserved'
    fi
  done

  # Uninstall may remove other owned entries, but must preserve the conflict.
  conflict_uninstall_output="$test_root/output-conflict-uninstall-$conflict_kind.txt"
  run_in_private_home "$conflict_uninstall_output" "$conflict_home" "$uninstall_script" --host codex
  assert_status 1 "uninstall reports protected entry ($conflict_kind)" "$conflict_uninstall_output"
  if [ "$conflict_kind" = directory ]; then
    [ -d "$conflict_shared/push" ] && [ ! -L "$conflict_shared/push" ] &&
      [ "$(cat "$conflict_shared/push/keep.txt")" = 'user-owned content' ] ||
      fail 'uninstall modified a user-owned directory'
    pass
  else
    assert_raw_link "$conflict_shared/push" "$conflict_source" 'uninstall preserves conflicting link'
  fi
done

# A first installation creates only the shared location. Compatibility support
# does not justify creating a legacy directory or adding missing legacy links.
fresh_home="$test_root/fresh-home"
mkdir "$fresh_home"
fresh_output="$test_root/output-fresh-home.txt"
run_in_private_home "$fresh_output" "$fresh_home" "$setup_script"
assert_status 0 'fresh shared-only installation' "$fresh_output"
assert_absent "$fresh_home/.codex" 'fresh installation creates no legacy directory'
for current_name in "${current_names[@]}"; do
  assert_link_resolves_to "$fresh_home/.agents/skills/$current_name" "$package_root/$current_name" \
    "fresh shared activation ($current_name)"
done

# CODEX_HOME is honored only inside this private fixture. Non-owned legacy
# entries are left alone and an absent package is not added to that target.
custom_home="$test_root/custom-home"
custom_codex="$test_root/custom-codex"
custom_legacy="$custom_codex/skills"
mkdir -p "$custom_home" "$custom_legacy/push"
printf '%s\n' 'legacy user directory' >"$custom_legacy/push/keep.txt"
ln -s "$repo_root/geo" "$custom_legacy/geo"
ln -s "$unrelated_dir" "$custom_legacy/repo"
custom_newline_source="$repo_root/todo"$'\n'
ln -s "$custom_newline_source" "$custom_legacy/todo"
for custom_mode in dry real repeat; do
  custom_output="$test_root/output-custom-$custom_mode.txt"
  if [ "$custom_mode" = dry ]; then
    run_in_private_home "$custom_output" "$custom_home" env CODEX_HOME="$custom_codex" "$setup_script" --dry-run
  else
    run_in_private_home "$custom_output" "$custom_home" env CODEX_HOME="$custom_codex" "$setup_script"
  fi
  assert_status 0 "custom legacy target ($custom_mode)" "$custom_output"
  if [ "$custom_mode" = dry ]; then
    assert_raw_link "$custom_legacy/geo" "$repo_root/geo" 'custom legacy dry-run preserves old link'
    assert_absent "$custom_home/.agents" 'custom dry-run creates no shared directory'
  else
    assert_link_resolves_to "$custom_legacy/geo" "$package_root/geo" 'custom legacy migrates owned link'
  fi
  assert_absent "$custom_legacy/build" 'custom legacy receives no missing package'
  assert_absent "$custom_home/.codex" 'custom CODEX_HOME leaves default legacy directory absent'
  assert_raw_link "$custom_legacy/repo" "$unrelated_dir" 'foreign legacy link preserved'
  assert_raw_link "$custom_legacy/todo" "$custom_newline_source" 'legacy newline lookalike preserved'
  [ -d "$custom_legacy/push" ] && [ ! -L "$custom_legacy/push" ] &&
    [ "$(cat "$custom_legacy/push/keep.txt")" = 'legacy user directory' ] ||
    fail 'setup changed a legacy user-owned directory'
  pass
done
assert_output_contains "$custom_output" 'Migrated: 0' 'custom legacy migration idempotence'

# Direct uninstall must recognize pre-layout same-name links in both locations,
# without requiring setup to repair them first. It also honors CODEX_HOME.
old_home="$test_root/direct-old-home"
old_shared="$old_home/.agents/skills"
old_codex="$test_root/direct-old-codex"
old_legacy="$old_codex/skills"
mkdir -p "$old_shared" "$old_legacy"
for old_target in "$old_shared" "$old_legacy"; do
  for current_name in "${current_names[@]}"; do
    ln -s "$repo_root/$current_name" "$old_target/$current_name"
  done
  for legacy_name in "${legacy_names[@]}"; do
    ln -s "$repo_root/$legacy_name" "$old_target/$legacy_name"
  done
done
old_dry_output="$test_root/output-direct-old-dry.txt"
run_in_private_home "$old_dry_output" "$old_home" env CODEX_HOME="$old_codex" "$uninstall_script" --host grok --dry-run
assert_status 0 'direct old-layout dual-target uninstall dry-run' "$old_dry_output"
for old_target in "$old_shared" "$old_legacy"; do
  for old_name in "${current_names[@]}" "${legacy_names[@]}"; do
    assert_raw_link "$old_target/$old_name" "$repo_root/$old_name" "direct old-layout dry-run ($old_name)"
  done
done
old_output="$test_root/output-direct-old.txt"
run_in_private_home "$old_output" "$old_home" env CODEX_HOME="$old_codex" "$uninstall_script" --host grok
assert_status 0 'direct old-layout dual-target uninstall' "$old_output"
for old_target in "$old_shared" "$old_legacy"; do
  for old_name in "${current_names[@]}" "${legacy_names[@]}"; do
    assert_absent "$old_target/$old_name" "direct old-layout uninstall ($old_name)"
  done
done
assert_absent "$old_home/.codex" 'direct custom uninstall leaves default legacy directory absent'

# The default setup installs into the shared user directory and preserves
# owned Codex links by updating their source path. Uninstall removes both.
bridge_shared_target="$test_home/.agents/skills"
bridge_legacy_target="$test_home/.codex/skills"
mkdir -p "$bridge_legacy_target"
for current_name in "${current_names[@]}"; do
  ln -s "$repo_root/$current_name" "$bridge_legacy_target/$current_name"
done

bridge_setup_dry_output="$test_root/output-bridge-setup-dry.txt"
run_default_setup "$bridge_setup_dry_output" --host grok --dry-run
assert_status 0 'shared setup with legacy migration dry-run' "$bridge_setup_dry_output"
assert_absent "$bridge_shared_target" 'bridge dry-run creates no shared target'
for current_name in "${current_names[@]}"; do
  assert_raw_link "$bridge_legacy_target/$current_name" "$repo_root/$current_name" \
    "bridge setup dry-run ($current_name)"
done

bridge_setup_output="$test_root/output-bridge-setup.txt"
run_default_setup "$bridge_setup_output" --host grok
assert_status 0 'shared setup with legacy path migration' "$bridge_setup_output"
assert_output_contains \
  "$bridge_setup_output" \
  "Target: $bridge_shared_target" \
  'shared setup target'
for current_name in "${current_names[@]}"; do
  assert_link_resolves_to \
    "$bridge_shared_target/$current_name" \
    "$package_root/$current_name" \
    "shared activation ($current_name)"
  assert_link_resolves_to \
    "$bridge_legacy_target/$current_name" \
    "$package_root/$current_name" \
    "legacy path migration ($current_name)"
done

bridge_repeat_output="$test_root/output-bridge-repeat.txt"
run_default_setup "$bridge_repeat_output" --host grok
assert_status 0 'dual-target setup repeated' "$bridge_repeat_output"
assert_output_contains "$bridge_repeat_output" 'Installed: 0' 'dual-target setup idempotence'
assert_output_contains "$bridge_repeat_output" 'Migrated: 0' 'dual-target setup idempotence'

bridge_uninstall_dry_output="$test_root/output-bridge-uninstall-dry.txt"
run_default_uninstall "$bridge_uninstall_dry_output" --host grok --dry-run
assert_status 0 'dual-target uninstall dry-run' "$bridge_uninstall_dry_output"
assert_output_contains \
  "$bridge_uninstall_dry_output" \
  "Shared target: $bridge_shared_target" \
  'dual-target uninstall shared target'
assert_output_contains \
  "$bridge_uninstall_dry_output" \
  "Legacy Codex target: $bridge_legacy_target" \
  'dual-target uninstall legacy target'
for current_name in "${current_names[@]}"; do
  assert_link_resolves_to \
    "$bridge_shared_target/$current_name" \
    "$package_root/$current_name" \
    "dual-target uninstall dry-run shared ($current_name)"
  assert_link_resolves_to \
    "$bridge_legacy_target/$current_name" \
    "$package_root/$current_name" \
    "dual-target uninstall dry-run legacy ($current_name)"
done

bridge_uninstall_output="$test_root/output-bridge-uninstall.txt"
run_default_uninstall "$bridge_uninstall_output" --host grok
assert_status 0 'dual-target uninstall' "$bridge_uninstall_output"
for current_name in "${current_names[@]}"; do
  assert_absent \
    "$bridge_shared_target/$current_name" \
    "dual-target uninstall shared ($current_name)"
  assert_absent \
    "$bridge_legacy_target/$current_name" \
    "dual-target uninstall legacy ($current_name)"
done

# A small independent checkout proves discovery by package location, not by
# current skill names or a category enumeration. Even SKILL.md lookalikes in
# repository-support folders and packages nested under a category are ignored.
fixture_repo="$test_root/discovery-checkout"
fixture_home="$test_root/discovery-home"
fixture_shared="$fixture_home/.agents/skills"
mkdir -p "$fixture_repo/skills/plain" "$fixture_repo/skills/unmapped" \
  "$fixture_repo/skills/group/nested" "$fixture_repo/docs" \
  "$fixture_repo/scripts" "$fixture_repo/templates" "$fixture_repo/old-root" "$fixture_home"
fixture_repo=$(CDPATH= cd -P "$fixture_repo" && pwd)
cp "$setup_script" "$fixture_repo/setup"
cp "$uninstall_script" "$fixture_repo/uninstall"
printf '%s\n' '# Package without classification metadata' >"$fixture_repo/skills/plain/SKILL.md"
printf '%s\n' '---' 'name: unmapped' 'metadata:' '  treefolk-category: future-category' '---' \
  >"$fixture_repo/skills/unmapped/SKILL.md"
for nonpackage in docs scripts templates old-root skills/group/nested; do
  printf '%s\n' '# This is not a public package at skills/*/SKILL.md' >"$fixture_repo/$nonpackage/SKILL.md"
done
fixture_output="$test_root/output-discovery.txt"
run_in_private_home "$fixture_output" "$fixture_home" "$fixture_repo/setup"
assert_status 0 'package discovery independent of taxonomy' "$fixture_output"
for fixture_name in plain unmapped; do
  assert_link_resolves_to "$fixture_shared/$fixture_name" "$fixture_repo/skills/$fixture_name" \
    "fixture package activation ($fixture_name)"
done
for nonpackage in docs scripts templates old-root group nested; do
  assert_absent "$fixture_shared/$nonpackage" "auxiliary directory excluded ($nonpackage)"
done
fixture_uninstall_output="$test_root/output-discovery-uninstall.txt"
run_in_private_home "$fixture_uninstall_output" "$fixture_home" "$fixture_repo/uninstall" --host codex
assert_status 0 'package uninstall independent of taxonomy' "$fixture_uninstall_output"
for fixture_name in plain unmapped; do
  assert_absent "$fixture_shared/$fixture_name" "fixture package uninstall ($fixture_name)"
done

# Calling an acquired checkout through a directory alias must still recognize
# old links created from its physical location and write the new physical path.
# Exercise only setup/uninstall here; the bootstrap owns full archive validation.
fixture_alias="$test_root/discovery-alias"
ln -s "$fixture_repo" "$fixture_alias"
ln -s "$fixture_repo/plain" "$fixture_shared/plain"
fixture_alias_dry_output="$test_root/output-aliased-source-dry.txt"
run_in_private_home "$fixture_alias_dry_output" "$fixture_home" "$fixture_alias/setup" --dry-run
assert_status 0 'aliased checkout migration dry-run' "$fixture_alias_dry_output"
assert_raw_link "$fixture_shared/plain" "$fixture_repo/plain" 'aliased checkout dry-run preserves owned old link'
assert_absent "$fixture_shared/unmapped" 'aliased checkout dry-run installs no package'
fixture_alias_setup_output="$test_root/output-aliased-source-setup.txt"
run_in_private_home "$fixture_alias_setup_output" "$fixture_home" "$fixture_alias/setup"
assert_status 0 'aliased checkout migrates physical source ownership' "$fixture_alias_setup_output"
for fixture_name in plain unmapped; do
  assert_raw_link "$fixture_shared/$fixture_name" "$fixture_repo/skills/$fixture_name" \
    "aliased checkout records physical source ($fixture_name)"
done
fixture_alias_uninstall_output="$test_root/output-aliased-source-uninstall.txt"
run_in_private_home "$fixture_alias_uninstall_output" "$fixture_home" "$fixture_alias/uninstall" --host codex
assert_status 0 'aliased checkout removes physical source links' "$fixture_alias_uninstall_output"
for fixture_name in plain unmapped; do
  assert_absent "$fixture_shared/$fixture_name" "aliased checkout uninstall ($fixture_name)"
done

# A former root package path that now exists again belongs to current user
# content; exact path spelling alone no longer authorizes migration or removal.
mkdir "$fixture_repo/plain"
printf '%s\n' 'repurposed source' >"$fixture_repo/plain/keep.txt"
ln -s "$fixture_repo/plain" "$fixture_shared/plain"
fixture_reuse_output="$test_root/output-reused-root.txt"
run_in_private_home "$fixture_reuse_output" "$fixture_home" "$fixture_repo/setup"
assert_status 1 'repurposed root source blocks migration' "$fixture_reuse_output"
assert_raw_link "$fixture_shared/plain" "$fixture_repo/plain" 'repurposed source link preserved by setup'
assert_absent "$fixture_shared/unmapped" 'repurposed source conflict prevents partial installation'
fixture_reuse_uninstall_output="$test_root/output-reused-root-uninstall.txt"
run_in_private_home "$fixture_reuse_uninstall_output" "$fixture_home" "$fixture_repo/uninstall" --host codex
assert_status 1 'repurposed root source blocks uninstall' "$fixture_reuse_uninstall_output"
assert_raw_link "$fixture_shared/plain" "$fixture_repo/plain" 'repurposed source link preserved by uninstall'
[ "$(cat "$fixture_repo/plain/keep.txt")" = 'repurposed source' ] || fail 'repurposed source contents changed'
pass

# A historical alias can become a real public package again. Its normal layout
# migration must take precedence over the obsolete-name cleanup rule.
unlink "$fixture_shared/plain"
mkdir -p "$fixture_repo/skills/push" "$fixture_repo/skills/c-push"
printf '%s\n' '# Current push package' >"$fixture_repo/skills/push/SKILL.md"
printf '%s\n' '# A new package intentionally reuses this old name' >"$fixture_repo/skills/c-push/SKILL.md"
ln -s "$fixture_repo/c-push" "$fixture_shared/c-push"
fixture_alias_output="$test_root/output-reused-alias.txt"
run_in_private_home "$fixture_alias_output" "$fixture_home" "$fixture_repo/setup"
assert_status 0 'live public package takes precedence over old alias cleanup' "$fixture_alias_output"
assert_link_resolves_to "$fixture_shared/c-push" "$fixture_repo/skills/c-push" 'reused alias package activated'
fixture_alias_uninstall_output="$test_root/output-reused-alias-uninstall.txt"
run_in_private_home "$fixture_alias_uninstall_output" "$fixture_home" "$fixture_repo/uninstall" --host codex
assert_status 0 'reused alias uninstalls as a current package' "$fixture_alias_uninstall_output"
assert_absent "$fixture_shared/c-push" 'reused alias package uninstalled'

# A public rename spans both source layouts and both activation locations.
# Keep this fixture independent of the live package list so the old name is
# always absent and the replacement is the only package that can be activated.
rename_repo="$test_root/rename-checkout"
mkdir -p "$rename_repo/skills/build"
rename_repo=$(CDPATH= cd -P "$rename_repo" && pwd)
cp "$setup_script" "$rename_repo/setup"
cp "$uninstall_script" "$rename_repo/uninstall"
printf '%s\n' '# Renamed implementation workflow' >"$rename_repo/skills/build/SKILL.md"
for former_layout in root nested; do
  if [ "$former_layout" = root ]; then
    former_source="$rename_repo/code-craft"
  else
    former_source="$rename_repo/skills/code-craft"
  fi
  for rename_action in setup uninstall conflict; do
    rename_home="$test_root/rename-$former_layout-$rename_action-home"
    rename_shared="$rename_home/.agents/skills"
    rename_codex="$test_root/rename-$former_layout-$rename_action-codex"
    rename_legacy="$rename_codex/skills"
    mkdir -p "$rename_shared" "$rename_legacy"
    for rename_target in "$rename_shared" "$rename_legacy"; do
      ln -s "$former_source" "$rename_target/code-craft"
    done
    if [ "$rename_action" = conflict ]; then
      mkdir "$rename_shared/build"
      printf '%s\n' 'user-owned replacement' >"$rename_shared/build/keep.txt"
    elif [ "$rename_action" = setup ] && [ "$former_layout" = nested ]; then
      # Cleanup must also run when the replacement was already activated.
      ln -s "$rename_repo/skills/build" "$rename_shared/build"
    fi
    for rename_mode in dry real; do
      rename_output="$test_root/output-rename-$former_layout-$rename_action-$rename_mode.txt"
      rename_args=()
      [ "$rename_mode" != dry ] || rename_args=(--dry-run)
      if [ "$rename_action" = uninstall ]; then
        run_in_private_home "$rename_output" "$rename_home" env CODEX_HOME="$rename_codex" \
          "$rename_repo/uninstall" --host codex ${rename_args[@]+"${rename_args[@]}"}
      else
        run_in_private_home "$rename_output" "$rename_home" env CODEX_HOME="$rename_codex" \
          "$rename_repo/setup" --host grok ${rename_args[@]+"${rename_args[@]}"}
      fi
      if [ "$rename_action" = conflict ]; then
        assert_status 1 "rename conflict ($former_layout, $rename_mode)" "$rename_output"
        [ ! -L "$rename_shared/build" ] &&
          [ "$(cat "$rename_shared/build/keep.txt")" = 'user-owned replacement' ] ||
          fail 'rename changed replacement conflict contents'
        pass
      else
        assert_status 0 "rename $rename_action ($former_layout, $rename_mode)" "$rename_output"
      fi
      for rename_target in "$rename_shared" "$rename_legacy"; do
        if [ "$rename_mode" = dry ] || [ "$rename_action" = conflict ]; then
          assert_raw_link "$rename_target/code-craft" "$former_source" 'rename preserves old link before successful activation'
        else
          assert_absent "$rename_target/code-craft" "rename $rename_action removes owned old name"
        fi
      done
      if [ "$rename_action" = setup ] && { [ "$rename_mode" = real ] || [ "$former_layout" = nested ]; }; then
        assert_link_resolves_to "$rename_shared/build" "$rename_repo/skills/build" 'renamed workflow activated'
      elif [ "$rename_action" != conflict ]; then
        assert_absent "$rename_shared/build" 'rename dry-run or direct uninstall creates no replacement'
      fi
      assert_absent "$rename_legacy/build" 'rename adds no legacy compatibility package'
      assert_absent "$rename_home/.codex" 'rename honors custom CODEX_HOME'
    done
    if [ "$rename_action" = setup ]; then
      run_in_private_home "$rename_output" "$rename_home" env CODEX_HOME="$rename_codex" "$rename_repo/setup"
      assert_status 0 "rename repeat ($former_layout)" "$rename_output"
      assert_output_contains "$rename_output" 'Installed: 0' 'rename repeat installs nothing'
      assert_output_contains "$rename_output" 'Migrated: 0' 'rename repeat migrates nothing'
    fi
  done
done

# A target name alone is not ownership: preserve foreign links, lookalike
# paths and user directories, including entries in the legacy Codex target.
for protected_kind in foreign newline directory reused-root reused-nested reused-symlink; do
  protected_repo="$test_root/rename-protected-checkout-$protected_kind"
  mkdir -p "$protected_repo/skills/build"
  protected_repo=$(CDPATH= cd -P "$protected_repo" && pwd)
  cp "$setup_script" "$protected_repo/setup"
  cp "$uninstall_script" "$protected_repo/uninstall"
  printf '%s\n' '# Replacement package' >"$protected_repo/skills/build/SKILL.md"
  protected_home="$test_root/rename-protected-$protected_kind"
  protected_shared="$protected_home/.agents/skills"
  protected_legacy="$protected_home/.codex/skills"
  mkdir -p "$protected_shared" "$protected_legacy"
  case "$protected_kind" in
    foreign) protected_source="$unrelated_dir" ;;
    newline) protected_source="$protected_repo/skills/code-craft"$'\n' ;;
    reused-root) protected_source="$protected_repo/code-craft" ;;
    reused-nested|reused-symlink) protected_source="$protected_repo/skills/code-craft" ;;
    directory) protected_source= ;;
  esac
  case "$protected_kind" in
    reused-symlink) ln -s "$unrelated_dir" "$protected_source" ;;
    reused-*)
      mkdir "$protected_source"
      printf '%s\n' 'reused source' >"$protected_source/keep.txt"
      ;;
  esac
  for protected_target in "$protected_shared" "$protected_legacy"; do
    if [ "$protected_kind" = directory ]; then
      mkdir "$protected_target/code-craft"
      printf '%s\n' 'user-owned skill' >"$protected_target/code-craft/keep.txt"
    else
      ln -s "$protected_source" "$protected_target/code-craft"
    fi
  done
  for protected_action in setup uninstall; do
    protected_output="$test_root/output-rename-protected-$protected_kind-$protected_action.txt"
    run_in_private_home "$protected_output" "$protected_home" "$protected_repo/$protected_action" --host codex
    assert_status 0 "protected old name ($protected_kind, $protected_action)" "$protected_output"
    for protected_target in "$protected_shared" "$protected_legacy"; do
      if [ "$protected_kind" = directory ]; then
        [ ! -L "$protected_target/code-craft" ] &&
          [ "$(cat "$protected_target/code-craft/keep.txt")" = 'user-owned skill' ] ||
          fail 'rename modified a user-owned old-name directory'
        pass
      else
        assert_raw_link "$protected_target/code-craft" "$protected_source" 'rename preserves unowned old name'
      fi
    done
  done
done

printf 'PASS: setup regression checks completed (%d assertions).\n' "$check_count"
