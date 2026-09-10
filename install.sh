#!/bin/bash

set -euo pipefail

PROGRAM_NAME=treefolk-install
REPOSITORY=treefolk-ai/skills
DEFAULT_REF=main

usage() {
  cat <<'EOF'
Usage: install.sh --host codex|grok [options]
       install.sh --help

Download Treefolk Skills, validate the source, and activate every public skill.

Options:
  --host HOST        Accept codex or grok (required). Both activate the shared
                     user skill directory discovered by Codex and Grok.
  --ref REF          Download a branch, tag, or commit (default: main).
  --install-dir PATH Store source at PATH.
                     Default: ${TREEFOLK_HOME:-$HOME/.treefolk}/skills
  --dry-run          Print the complete plan without network or filesystem writes.
  --help, -h         Show this help message.

This bootstrap performs a first install only. It refuses to overwrite or update
an existing source path. Host activation is delegated to the downloaded setup.
EOF
}

fail() {
  printf '%s: %s\n' "$PROGRAM_NAME" "$1" >&2
  exit 1
}

argument_error() {
  printf '%s: %s\n' "$PROGRAM_NAME" "$1" >&2
  printf 'Run install.sh --help for usage.\n' >&2
  exit 2
}

require_value() {
  [ "$#" -ge 2 ] || argument_error "$1 requires a value"
  [ -n "$2" ] || argument_error "$1 requires a non-empty value"
}

normalize_absolute_path() {
  local input_path

  input_path=$1
  case "$input_path" in
    /*) ;;
    *) input_path="$(pwd -P)/$input_path" ;;
  esac

  while [ "$input_path" != / ] && [ "${input_path%/}" != "$input_path" ]; do
    input_path=${input_path%/}
  done
  printf '%s\n' "$input_path"
}

resolve_activation_target() {
  local target

  if [ "${TREEFOLK_SKILLS_DIR+x}" = x ]; then
    [ -n "$TREEFOLK_SKILLS_DIR" ] || fail 'TREEFOLK_SKILLS_DIR is set but empty'
    target=$TREEFOLK_SKILLS_DIR
  else
    [ "${HOME+x}" = x ] && [ -n "$HOME" ] || fail 'HOME is not set'
    target="${HOME%/}/.agents/skills"
  fi

  normalize_absolute_path "$target"
}

validate_ref() {
  local candidate

  candidate=$1
  case "$candidate" in
    ''|/*|-*|*/|*..*|*//*|*\\*|*\?*|*\#*|*%*)
      argument_error "unsafe ref: $candidate"
      ;;
  esac
  if ! [[ "$candidate" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ ]]; then
    argument_error "unsafe ref: $candidate"
  fi
}

temporary_dir=
cleanup() {
  if [ -n "$temporary_dir" ] && [ -d "$temporary_dir" ]; then
    rm -rf -- "$temporary_dir"
  fi
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

host=
ref=$DEFAULT_REF
install_dir=
dry_run=0
host_seen=0
ref_seen=0
install_dir_seen=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --host)
      require_value "$@"
      [ "$host_seen" -eq 0 ] || argument_error '--host may be specified only once'
      host=$2
      host_seen=1
      shift 2
      ;;
    --host=*)
      [ "$host_seen" -eq 0 ] || argument_error '--host may be specified only once'
      host=${1#--host=}
      [ -n "$host" ] || argument_error '--host requires a non-empty value'
      host_seen=1
      shift
      ;;
    --ref)
      require_value "$@"
      [ "$ref_seen" -eq 0 ] || argument_error '--ref may be specified only once'
      ref=$2
      ref_seen=1
      shift 2
      ;;
    --ref=*)
      [ "$ref_seen" -eq 0 ] || argument_error '--ref may be specified only once'
      ref=${1#--ref=}
      [ -n "$ref" ] || argument_error '--ref requires a non-empty value'
      ref_seen=1
      shift
      ;;
    --install-dir)
      require_value "$@"
      [ "$install_dir_seen" -eq 0 ] || argument_error '--install-dir may be specified only once'
      install_dir=$2
      install_dir_seen=1
      shift 2
      ;;
    --install-dir=*)
      [ "$install_dir_seen" -eq 0 ] || argument_error '--install-dir may be specified only once'
      install_dir=${1#--install-dir=}
      [ -n "$install_dir" ] || argument_error '--install-dir requires a non-empty value'
      install_dir_seen=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      argument_error "unknown argument: $1"
      ;;
  esac
done

[ -n "$host" ] || argument_error '--host codex or --host grok is required'
case "$host" in
  codex|grok) ;;
  *) argument_error "unsupported host: $host (expected codex or grok)" ;;
esac
validate_ref "$ref"

if [ -z "$install_dir" ]; then
  if [ "${TREEFOLK_HOME+x}" = x ]; then
    [ -n "$TREEFOLK_HOME" ] || fail 'TREEFOLK_HOME is set but empty'
    install_dir="${TREEFOLK_HOME%/}/skills"
  else
    [ "${HOME+x}" = x ] && [ -n "$HOME" ] || fail 'HOME is not set'
    install_dir="${HOME%/}/.treefolk/skills"
  fi
fi

install_dir=$(normalize_absolute_path "$install_dir")
[ "$install_dir" != / ] || fail 'the source install directory must not be /'
activation_target=$(resolve_activation_target)
archive_url="https://codeload.github.com/$REPOSITORY/tar.gz/$ref"

printf 'Repository: %s\n' "$REPOSITORY"
printf 'Ref: %s\n' "$ref"
printf 'Archive: %s\n' "$archive_url"
printf 'Source install directory: %s\n' "$install_dir"
printf 'Host: %s\n' "$host"
printf 'Activation target: %s\n' "$activation_target"

if [ -e "$install_dir" ] || [ -L "$install_dir" ]; then
  fail "source install path already exists; refusing to overwrite or update: $install_dir"
fi

printf 'Plan:\n'
printf '  1. Download the selected source archive over HTTPS.\n'
printf '  2. Extract it in a private temporary directory.\n'
printf '  3. Check Bash syntax, skill packages, and setup behavior in a private temporary target.\n'
printf '  4. Create the new source install directory without overwriting anything.\n'
printf '  5. Delegate shared user-skill activation to the downloaded setup script.\n'

if [ "$dry_run" -eq 1 ]; then
  printf 'Mode: dry-run (no network or filesystem writes)\n'
  printf 'Result: plan is safe to attempt; nothing was downloaded or installed.\n'
  exit 0
fi

printf 'Mode: install\n'
for required_command in curl tar mktemp mkdir mv; do
  command -v "$required_command" >/dev/null 2>&1 || fail "required command not found: $required_command"
done

temporary_base=${TMPDIR:-/tmp}
temporary_base=${temporary_base%/}
[ -n "$temporary_base" ] || temporary_base=/tmp
temporary_dir=$(mktemp -d "$temporary_base/treefolk-skills.XXXXXX") || fail 'could not create a private temporary directory'
archive_file="$temporary_dir/source.tar.gz"
archive_list="$temporary_dir/archive.list"
extracted_dir="$temporary_dir/source"
mkdir "$extracted_dir"

printf 'Downloading source...\n'
if ! curl -fsSL --proto '=https' "$archive_url" -o "$archive_file"; then
  fail 'download failed; no source was installed or activated'
fi

if ! tar -tzf "$archive_file" >"$archive_list"; then
  fail 'downloaded archive is not a readable gzip tar archive'
fi
while IFS= read -r archive_entry; do
  case "$archive_entry" in
    /*|../*|*/../*|*/..)
      fail "archive contains an unsafe path: $archive_entry"
      ;;
  esac
done <"$archive_list"

if ! tar -xzf "$archive_file" -C "$extracted_dir" --strip-components=1; then
  fail 'archive extraction failed; no source was installed or activated'
fi

for required_file in install.sh setup uninstall scripts/check-setup.sh scripts/check-skills.sh; do
  [ -f "$extracted_dir/$required_file" ] || fail "downloaded source is missing required file: $required_file"
done

if ! /bin/bash -n "$extracted_dir/install.sh" ||
   ! /bin/bash -n "$extracted_dir/setup" ||
   ! /bin/bash -n "$extracted_dir/uninstall" ||
   ! /bin/bash -n "$extracted_dir/scripts/check-setup.sh" ||
   ! /bin/bash -n "$extracted_dir/scripts/check-skills.sh"; then
  fail 'downloaded source failed Bash syntax validation'
fi

shopt -s nullglob
downloaded_skills=("$extracted_dir"/skills/*/SKILL.md)
shopt -u nullglob
[ "${#downloaded_skills[@]}" -gt 0 ] || fail 'downloaded source contains no skills/*/SKILL.md packages'

if ! /bin/bash "$extracted_dir/scripts/check-skills.sh"; then
  fail 'downloaded source failed skill-package validation'
fi

if ! /bin/bash "$extracted_dir/scripts/check-setup.sh"; then
  fail 'downloaded source failed setup behavior validation'
fi

if [ -e "$install_dir" ] || [ -L "$install_dir" ]; then
  fail "source install path appeared during validation; refusing to overwrite it: $install_dir"
fi

install_parent=${install_dir%/*}
[ -n "$install_parent" ] || install_parent=/
mkdir -p "$install_parent"
if ! mkdir "$install_dir"; then
  fail "could not claim the new source install directory without overwriting it: $install_dir"
fi

shopt -s dotglob nullglob
source_entries=("$extracted_dir"/*)
shopt -u dotglob nullglob
[ "${#source_entries[@]}" -gt 0 ] || fail "validated source unexpectedly became empty; inspect $install_dir before retrying"
for source_entry in "${source_entries[@]}"; do
  if ! mv "$source_entry" "$install_dir/"; then
    fail "source installation is incomplete at $install_dir; inspect it before retrying"
  fi
done

printf 'Source installed: %s\n' "$install_dir"
printf 'Activating skills for %s...\n' "$host"
if ! /bin/bash "$install_dir/setup" --host "$host"; then
  fail "source is installed at $install_dir, but host activation failed; resolve the reported conflict and rerun its setup"
fi

if ! /bin/bash "$install_dir/setup" --host "$host" --dry-run; then
  fail "activation ran, but verification failed; inspect $install_dir and $activation_target"
fi

printf 'Installation complete: source validated and all public skills activated for %s.\n' "$host"
