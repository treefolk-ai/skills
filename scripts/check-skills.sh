#!/bin/bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/check-skills.sh [--help]

Validate every top-level */SKILL.md package in this repository.
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
      }
    }
    END {
      for (index_value = 1; index_value <= candidate_count; index_value++) {
        if (candidate_indent[index_value] == minimum_indent) {
          direct = 1
          if (candidate_nonempty[index_value]) {
            valid = 1
          }
        }
      }
      if (valid) {
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

shopt -s nullglob
skill_files=("$repo_root"/*/SKILL.md)
shopt -u nullglob

if [ "${#skill_files[@]}" -eq 0 ]; then
  report_error "." "no top-level */SKILL.md files found"
fi

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
done

if [ "$error_count" -gt 0 ]; then
  printf 'Validation failed: checked %d skill package(s); found %d error(s).\n' "$checked_count" "$error_count" >&2
  exit 1
fi

printf 'Validation passed: checked %d top-level skill package(s); found 0 errors.\n' "$checked_count"
