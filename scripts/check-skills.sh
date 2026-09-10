#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/check-skills.sh [--help]

Validate every skills/*/SKILL.md package and required Codex adapter in this repository.
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

export LC_ALL=C

error_count=0
checked_count=0
declared_names=()
declared_name_files=()

required_sections=(
  "Outcome"
  "Use when"
  "Do not use when"
  "Inputs"
  "Preconditions"
  "Workflow"
  "Stop conditions"
  "Safety"
  "Verification"
  "Completion report"
)

explicit_only_skills=(
  "deploy"
  "grill"
  "loop"
  "pr"
  "push"
  "repo"
)

report_error() {
  local file=$1
  local reason=$2

  printf 'ERROR [%s]: %s\n' "$file" "$reason" >&2
  error_count=$((error_count + 1))
}

top_level_field_present() {
  local file=$1
  local frontmatter_end=$2
  local field=$3

  awk -v last="$frontmatter_end" -v field="$field" '
    NR >= last { exit }
    NR > 1 {
      sub(/\r$/, "")
      if (index($0, field ":") == 1) {
        found = 1
        exit
      }
    }
    END { exit(found ? 0 : 1) }
  ' "$file"
}

top_level_scalar() {
  local file=$1
  local frontmatter_end=$2
  local field=$3

  awk -v last="$frontmatter_end" -v field="$field" '
    function trim(value) {
      sub(/^[ \t]+/, "", value)
      sub(/[ \t]+$/, "", value)
      return value
    }
    NR >= last { exit }
    NR > 1 && index($0, field ":") == 1 {
      value = substr($0, length(field) + 2)
      sub(/\r$/, "", value)
      sub(/[ \t]+#.*/, "", value)
      value = trim(value)
      if (length(value) >= 2) {
        first = substr(value, 1, 1)
        final = substr(value, length(value), 1)
        if ((first == "\"" && final == "\"") || (first == "\047" && final == "\047")) {
          value = substr(value, 2, length(value) - 2)
        }
      }
      print value
      exit
    }
  ' "$file"
}

top_level_field_nonempty() {
  local file=$1
  local frontmatter_end=$2
  local field=$3

  awk -v last="$frontmatter_end" -v field="$field" '
    function trim(value) {
      sub(/^[ \t]+/, "", value)
      sub(/[ \t]+$/, "", value)
      return value
    }
    NR >= last { exit }
    in_block {
      line = $0
      sub(/\r$/, "", line)
      if (line !~ /^[ \t]/ && line !~ /^[ \t]*$/ && line !~ /^#/) {
        exit
      }
      if (line ~ /^[ \t]/ && trim(line) != "") {
        nonempty = 1
      }
      next
    }
    NR > 1 && index($0, field ":") == 1 {
      found = 1
      value = substr($0, length(field) + 2)
      sub(/\r$/, "", value)
      sub(/[ \t]+#.*/, "", value)
      value = trim(value)
      if (value ~ /^[>|][0-9+-]*$/) {
        in_block = 1
        next
      }
      if (length(value) >= 2) {
        first = substr(value, 1, 1)
        final = substr(value, length(value), 1)
        if ((first == "\"" && final == "\"") || (first == "\047" && final == "\047")) {
          value = substr(value, 2, length(value) - 2)
        }
      }
      if (trim(value) != "") {
        nonempty = 1
      }
      exit
    }
    END { exit(found && nonempty ? 0 : 1) }
  ' "$file"
}

metadata_mapping_status() {
  local file=$1
  local frontmatter_end=$2

  awk -v last="$frontmatter_end" '
    function trim(value) {
      sub(/^[ \t]+/, "", value)
      sub(/[ \t]+$/, "", value)
      return value
    }
    NR >= last { exit }
    NR > 1 && index($0, "metadata:") == 1 {
      found = 1
      value = substr($0, 10)
      sub(/\r$/, "", value)
      sub(/[ \t]+#.*/, "", value)
      if (trim(value) != "") {
        inline_value = 1
      }
      exit
    }
    END {
      if (!found) {
        print "missing"
      } else if (inline_value) {
        print "not-mapping"
      } else {
        print "ok"
      }
    }
  ' "$file"
}

metadata_key_status() {
  local file=$1
  local frontmatter_end=$2
  local key=$3

  awk -v last="$frontmatter_end" -v key="$key" '
    function trim(value) {
      sub(/^[ \t]+/, "", value)
      sub(/[ \t]+$/, "", value)
      return value
    }
    NR >= last { exit }
    !in_metadata && index($0, "metadata:") == 1 {
      in_metadata = 1
      next
    }
    in_metadata {
      line = $0
      sub(/\r$/, "", line)
      if (line ~ /^[ \t]*$/ || line ~ /^[ \t]*#/) {
        next
      }
      match(line, /^ */)
      indent = RLENGTH
      if (indent == 0) {
        exit
      }
      if (!minimum_indent || indent < minimum_indent) {
        minimum_indent = indent
      }
      content = substr(line, indent + 1)
      if (index(content, key ":") == 1) {
        candidate_count++
        candidate_indent[candidate_count] = indent
        value = substr(content, length(key) + 2)
        sub(/[ \t]+#.*/, "", value)
        value = trim(value)
        if (length(value) >= 2) {
          first = substr(value, 1, 1)
          final = substr(value, length(value), 1)
          if ((first == "\"" && final == "\"") || (first == "\047" && final == "\047")) {
            value = substr(value, 2, length(value) - 2)
          }
        }
        candidate_nonempty[candidate_count] = (trim(value) != "")
        candidate_supported[candidate_count] = (key != "treefolk-category" || value == "think" || value == "make" || value == "share")
      }
    }
    END {
      for (index_value = 1; index_value <= candidate_count; index_value++) {
        if (candidate_indent[index_value] == minimum_indent) {
          direct = 1
          if (candidate_nonempty[index_value]) {
            valid = 1
            if (candidate_supported[index_value]) {
              supported = 1
            }
          }
        }
      }
      if (valid && !supported) {
        print "unsupported"
      } else if (valid) {
        print "ok"
      } else if (direct) {
        print "empty"
      } else if (candidate_count) {
        print "not-direct"
      } else {
        print "missing"
      }
    }
  ' "$file"
}

section_count() {
  local file=$1
  local content_start=$2
  local section=$3

  awk -v first="$content_start" -v heading="## $section" '
    NR >= first {
      sub(/\r$/, "")
      if ($0 == heading) {
        count++
      }
    }
    END { print count + 0 }
  ' "$file"
}

requires_explicit_invocation() {
  local skill_name=$1
  local candidate

  for candidate in "${explicit_only_skills[@]}"; do
    if [ "$skill_name" = "$candidate" ]; then
      return 0
    fi
  done

  return 1
}

top_level_mapping_count() {
  local file=$1
  local mapping=$2

  awk -v heading="$mapping:" '
    {
      sub(/\r$/, "")
      if ($0 == heading) {
        count++
      }
    }
    END { print count + 0 }
  ' "$file"
}

direct_nested_key_count() {
  local file=$1
  local mapping=$2
  local key=$3

  awk -v heading="$mapping:" -v prefix="  $key:" '
    {
      sub(/\r$/, "")
    }
    $0 == heading {
      in_mapping = 1
      next
    }
    in_mapping && $0 !~ /^[ \t]/ && $0 !~ /^$/ && $0 !~ /^#/ {
      in_mapping = 0
    }
    in_mapping && index($0, prefix) == 1 {
      count++
    }
    END { print count + 0 }
  ' "$file"
}

direct_nested_raw_value() {
  local file=$1
  local mapping=$2
  local key=$3

  awk -v heading="$mapping:" -v prefix="  $key:" '
    function trim(value) {
      sub(/^[ \t]+/, "", value)
      sub(/[ \t]+$/, "", value)
      return value
    }
    {
      sub(/\r$/, "")
    }
    $0 == heading {
      in_mapping = 1
      next
    }
    in_mapping && $0 !~ /^[ \t]/ && $0 !~ /^$/ && $0 !~ /^#/ {
      exit
    }
    in_mapping && index($0, prefix) == 1 {
      print trim(substr($0, length(prefix) + 1))
      exit
    }
  ' "$file"
}

validate_explicit_only_adapter() {
  local skill_name=$1
  local package_dir=$2
  local adapter_file="$package_dir/agents/openai.yaml"
  local relative_adapter=${adapter_file#"$repo_root"/}
  local mapping
  local mapping_count
  local key
  local key_count
  local raw_value
  local scalar_value
  local expected_mention

  if [ ! -f "$adapter_file" ]; then
    report_error "$relative_adapter" "P0 skill '$skill_name' requires a Codex adapter"
    return
  fi

  for mapping in interface policy; do
    mapping_count=$(top_level_mapping_count "$adapter_file" "$mapping")
    if [ "$mapping_count" -ne 1 ]; then
      report_error "$relative_adapter" "top-level mapping '$mapping' must appear exactly once"
    fi
  done

  for key in display_name short_description default_prompt; do
    key_count=$(direct_nested_key_count "$adapter_file" interface "$key")
    if [ "$key_count" -ne 1 ]; then
      report_error "$relative_adapter" "interface key '$key' must appear exactly once with two-space indentation"
      continue
    fi

    raw_value=$(direct_nested_raw_value "$adapter_file" interface "$key")
    case "$raw_value" in
      \"*\")
        scalar_value=${raw_value#\"}
        scalar_value=${scalar_value%\"}
        if [ -z "$scalar_value" ]; then
          report_error "$relative_adapter" "interface key '$key' must not be empty"
        fi
        ;;
      *)
        report_error "$relative_adapter" "interface key '$key' must be a quoted string"
        continue
        ;;
    esac

    if [ "$key" = "short_description" ] && { [ "${#scalar_value}" -lt 25 ] || [ "${#scalar_value}" -gt 64 ]; }; then
      report_error "$relative_adapter" "interface.short_description must contain 25-64 characters"
    fi

    if [ "$key" = "default_prompt" ]; then
      expected_mention="\$$skill_name"
      case "$scalar_value" in
        *"$expected_mention") ;;
        *"$expected_mention"[!a-z0-9-]*) ;;
        *) report_error "$relative_adapter" "interface.default_prompt must mention '$expected_mention'" ;;
      esac
    fi
  done

  key_count=$(direct_nested_key_count "$adapter_file" policy allow_implicit_invocation)
  if [ "$key_count" -ne 1 ]; then
    report_error "$relative_adapter" "policy.allow_implicit_invocation must appear exactly once with two-space indentation"
  else
    raw_value=$(direct_nested_raw_value "$adapter_file" policy allow_implicit_invocation)
    if [ "$raw_value" != "false" ]; then
      report_error "$relative_adapter" "P0 skill '$skill_name' requires unquoted policy.allow_implicit_invocation: false"
    fi
  fi
}

shopt -s nullglob
skill_files=("$repo_root"/skills/*/SKILL.md)
shopt -u nullglob

if [ "${#skill_files[@]}" -eq 0 ]; then
  report_error "skills" "no skills/*/SKILL.md files found"
fi

for explicit_only_skill in "${explicit_only_skills[@]}"; do
  if [ ! -f "$repo_root/skills/$explicit_only_skill/SKILL.md" ]; then
    report_error "scripts/check-skills.sh" "P0 skill '$explicit_only_skill' does not name an existing package in skills/"
  fi
done

for skill_file in "${skill_files[@]}"; do
  checked_count=$((checked_count + 1))
  relative_file=${skill_file#"$repo_root"/}
  package_dir=$(basename -- "$(dirname -- "$skill_file")")
  frontmatter_end=""
  content_start=1

  first_line=$(awk 'NR == 1 { sub(/\r$/, ""); print; exit }' "$skill_file")
  if [ "$first_line" != "---" ]; then
    report_error "$relative_file" "YAML frontmatter must begin with --- on line 1"
  else
    frontmatter_end=$(awk 'NR > 1 { sub(/\r$/, ""); if ($0 == "---") { print NR; exit } }' "$skill_file")
    if [ -z "$frontmatter_end" ]; then
      report_error "$relative_file" "YAML frontmatter is not closed with ---"
    else
      content_start=$((frontmatter_end + 1))
    fi
  fi

  if [ -n "$frontmatter_end" ]; then
    skill_name=""
    if ! top_level_field_present "$skill_file" "$frontmatter_end" "name"; then
      report_error "$relative_file" "missing top-level frontmatter field 'name'"
    else
      skill_name=$(top_level_scalar "$skill_file" "$frontmatter_end" "name")
      if [ -z "$skill_name" ]; then
        report_error "$relative_file" "frontmatter field 'name' must not be empty"
      else
        if ! [[ "$skill_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
          report_error "$relative_file" "name '$skill_name' must use lowercase kebab-case"
        fi
        if [ "$skill_name" != "$package_dir" ]; then
          report_error "$relative_file" "name '$skill_name' does not match parent directory '$package_dir'"
        fi

        duplicate_index=0
        while [ "$duplicate_index" -lt "${#declared_names[@]}" ]; do
          if [ "${declared_names[$duplicate_index]}" = "$skill_name" ]; then
            report_error "$relative_file" "duplicate name '$skill_name' (also declared in ${declared_name_files[$duplicate_index]})"
            break
          fi
          duplicate_index=$((duplicate_index + 1))
        done
        declared_names[${#declared_names[@]}]=$skill_name
        declared_name_files[${#declared_name_files[@]}]=$relative_file
      fi
    fi

    if ! top_level_field_present "$skill_file" "$frontmatter_end" "description"; then
      report_error "$relative_file" "missing top-level frontmatter field 'description'"
    elif ! top_level_field_nonempty "$skill_file" "$frontmatter_end" "description"; then
      report_error "$relative_file" "frontmatter field 'description' must not be empty"
    fi

    metadata_status=$(metadata_mapping_status "$skill_file" "$frontmatter_end")
    case "$metadata_status" in
      missing)
        report_error "$relative_file" "missing top-level frontmatter mapping 'metadata'"
        ;;
      not-mapping)
        report_error "$relative_file" "frontmatter field 'metadata' must be a nested mapping"
        ;;
      ok)
        for metadata_key in treefolk-category treefolk-domain treefolk-kind; do
          key_status=$(metadata_key_status "$skill_file" "$frontmatter_end" "$metadata_key")
          case "$key_status" in
            missing)
              report_error "$relative_file" "missing nested metadata key '$metadata_key'"
              ;;
            not-direct)
              report_error "$relative_file" "metadata key '$metadata_key' must be directly nested under 'metadata'"
              ;;
            empty)
              report_error "$relative_file" "nested metadata key '$metadata_key' must not be empty"
              ;;
            unsupported)
              report_error "$relative_file" "treefolk-category must be think, make, or share"
              ;;
          esac
        done
        ;;
    esac
  fi

  for required_section in "${required_sections[@]}"; do
    heading_count=$(section_count "$skill_file" "$content_start" "$required_section")
    if [ "$heading_count" -eq 0 ]; then
      report_error "$relative_file" "missing exact H2 heading '## $required_section'"
    elif [ "$heading_count" -gt 1 ]; then
      report_error "$relative_file" "H2 heading '## $required_section' appears $heading_count times"
    fi
  done

  if requires_explicit_invocation "$package_dir"; then
    validate_explicit_only_adapter "$package_dir" "$(dirname -- "$skill_file")"
  fi
done

if [ "$error_count" -gt 0 ]; then
  printf 'Validation failed: checked %d skill package(s); found %d error(s).\n' "$checked_count" "$error_count" >&2
  exit 1
fi

printf 'Validation passed: checked %d skill package(s) in skills/; found 0 errors.\n' "$checked_count"
