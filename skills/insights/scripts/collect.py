#!/usr/bin/env python3
"""Read Codex rollouts into dated counts and a bounded, redacted evidence sample.

Standard library only. Never executes transcript content or makes network calls.
"""

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from storage import create_report_dir, new_file, report_root
from context import load_context
from tokens import TokenCounter, add_tokens, empty_totals, summarize

MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_LINE_BYTES = 1024 * 1024
MAX_FILES = 2000
GAPS = {"file_limit_excluded", "truncated_files", "oversized_or_cut_lines", "malformed_lines", "undated_records", "unreadable_files", "unreadable_directories", "unsupported_files", "unsupported_call_ids", "unknown_tool_names", "unknown_project_files"}


def timestamp(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result if result.tzinfo else None
    except ValueError:
        return None


def excerpt(text):
    """Best-effort minimization, deliberately not an anonymization guarantee."""
    if re.search(r"(?i)(api[_-]?key|password|secret|authorization|bearer|token)\s*[:= ]\s*\S+|\bsk-[\w-]{12,}|BEGIN .*PRIVATE KEY", text):
        return "[疑似敏感内容已省略]"
    text = re.sub(r"```[\s\S]*?(?:```|$)", "[代码块省略]", text)
    text = re.sub(r"https?://\S+", "[链接]", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[邮箱]", text)
    text = re.sub(r"(?:/(?:Users|home|private|tmp)/|[A-Za-z]:\\)[^\s`'\"<>]+", "[路径]", text)
    return " ".join(text.split())[:240]


def records(path, coverage):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("source is not a regular file")
        budget = min(info.st_size, MAX_FILE_BYTES)
        if info.st_size > budget:
            coverage["truncated_files"] += 1
        line_number = 0
        while stream.tell() < budget:
            line_number += 1
            raw = stream.readline(min(MAX_LINE_BYTES + 1, budget - stream.tell()))
            if len(raw) > MAX_LINE_BYTES or (not raw.endswith(b"\n") and stream.tell() < info.st_size):
                coverage["oversized_or_cut_lines"] += 1
                # Do not parse the tail of an oversized line as a new record.
                while raw and not raw.endswith(b"\n") and stream.tell() < budget:
                    raw = stream.readline(min(MAX_LINE_BYTES, budget - stream.tell()))
                continue
            try:
                record = json.loads(raw)
                if not isinstance(record, dict):
                    raise ValueError("not an object")
                yield line_number, record
            except (ValueError, UnicodeError):
                coverage["malformed_lines"] += 1


def command_family(payload):
    tool_name = payload.get("name")
    if not isinstance(tool_name, str) or tool_name.split(".")[-1] not in {"exec_command", "shell_command", "shell"}:
        return None
    try:
        args = payload.get("arguments", {})
        args = json.loads(args) if isinstance(args, str) else args
        if not isinstance(args, dict):
            return None
        cmd = args.get("cmd", args.get("command", ""))
        if isinstance(cmd, list):
            cmd = " ".join(str(item) for item in cmd)
        if not isinstance(cmd, str) or not cmd:
            return None
        if re.search(r"[\n;|&`]|\$\(", cmd):
            return "复合 shell 命令"
        words = shlex.split(cmd)
        while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
            words.pop(0)
        if not words:
            return None
        name = Path(words[0]).name
        if not re.fullmatch(r"[A-Za-z0-9_.+-]{1,40}", name):
            return "其他 shell 命令"
        if name in {"git", "codex", "pnpm", "npm", "yarn"} and len(words) > 1 and re.fullmatch(r"[a-z][a-z-]{0,24}", words[1]):
            return name + " " + words[1]
        return name
    except (ValueError, TypeError):
        return None


def failed(payload):
    if payload.get("is_error") is True or payload.get("isError") is True:
        return True
    output = payload.get("output")
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except ValueError:
            match = re.search(r"(?:Process exited with code|exit_code\s*[:=])\s*(-?\d+)", output)
            return bool(match and int(match.group(1)) != 0)
    if isinstance(output, dict):
        code = output.get("exit_code")
        return output.get("isError") is True or output.get("is_error") is True or (type(code) is int and code != 0)
    return False


def user_text(payload):
    content = payload.get("content", [])
    if not isinstance(content, list):
        return ""
    text = "\n".join(part.get("text", "") for part in content if isinstance(part, dict) and isinstance(part.get("text"), str))
    if text.lstrip().startswith(("# AGENTS.md instructions", "<environment_context>", "<INSTRUCTIONS>")):
        return ""
    return text


def read_session(path, root, start, end, tz, project, coverage):
    metadata = None
    events, fallback = [], []
    canonical_users = False
    seen_calls = set()
    seen_results = set()
    tokens = TokenCounter()
    token_time = None
    for line, record in records(path, coverage):
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        outer, kind = record.get("type"), payload.get("type")
        if outer == "session_meta":
            metadata = payload
            source = payload.get("source")
            if isinstance(source, dict) and "subagent" in source:
                coverage["subagent_files"] += 1
                return None
            cwd = payload.get("cwd")
            if project and (not isinstance(cwd, str) or not os.path.isabs(cwd) or os.path.commonpath([os.path.normpath(cwd), project]) != project):
                coverage["outside_project"] += 1
                return None
            continue
        if outer == "event_msg" and kind == "user_message":
            canonical_users = True
        observed = timestamp(record.get("timestamp"))
        if observed is None:
            coverage["undated_records"] += 1
            if outer == "event_msg" and kind == "token_count":
                tokens.previous = None
            continue
        day = observed.astimezone(tz).date()
        if outer == "event_msg" and kind == "token_count":
            if token_time is not None and observed < token_time:
                tokens.previous = None
                delta = {"coverage": {"snapshots": 1, "out_of_order": 1}}
            else:
                delta = tokens.read(payload)
            token_time = max(observed, token_time) if token_time else observed
            if start <= day <= end:
                events.append({"date": day.isoformat(), "line": line, "kind": "tokens", "tokens": delta})
            continue
        if not start <= day <= end:
            continue
        item = {"date": day.isoformat(), "line": line}
        if outer == "event_msg" and kind == "user_message" and isinstance(payload.get("message"), str):
            events.append(dict(item, kind="request", text=payload["message"]))
        elif outer == "response_item" and kind == "message" and payload.get("role") == "user":
            text = user_text(payload)
            if text:
                fallback.append(dict(item, kind="request", text=text))
        elif outer == "response_item" and kind in {"function_call", "custom_tool_call"}:
            call_id = payload.get("call_id")
            if call_id is not None and not isinstance(call_id, str):
                coverage["unsupported_call_ids"] += 1
                call_id = None
            if call_id and call_id in seen_calls:
                coverage["duplicate_calls"] += 1
                continue
            if call_id:
                seen_calls.add(call_id)
            name = payload.get("name")
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", name):
                coverage["unknown_tool_names"] += 1
                name = "unknown"
            events.append(dict(item, kind="tool", text=name, command=command_family(payload)))
        elif outer == "response_item" and kind in {"function_call_output", "custom_tool_call_output"} and failed(payload):
            call_id = payload.get("call_id")
            if isinstance(call_id, str):
                if call_id in seen_results:
                    coverage["duplicate_results"] += 1
                    continue
                seen_results.add(call_id)
            events.append(dict(item, kind="error", text="工具结果记录了显式失败；原因需回看上下文"))
    if not metadata or not isinstance(metadata.get("id"), str):
        coverage["unsupported_files"] += 1
        return None
    if not canonical_users:
        events.extend(fallback)
        if fallback:
            coverage["fallback_message_files"] += 1
    if not events:
        coverage["outside_window_or_empty"] += 1
        return None
    cwd = metadata.get("cwd")
    if not isinstance(cwd, str):
        cwd = "unknown"
        coverage["unknown_project_files"] += 1
    return {"id": metadata["id"], "cwd": cwd, "source": str(path.relative_to(root)), "events": sorted(events, key=lambda item: item["line"])}


def collect(root, start, end, tz, project=None, max_files=MAX_FILES):
    root = Path(root).expanduser().resolve(strict=True)
    roots = [root / name for name in ("sessions", "archived_sessions") if (root / name).is_dir() and not (root / name).is_symlink()]
    if not roots:
        raise ValueError("source must contain a readable sessions/ or archived_sessions/ directory")
    coverage = Counter()
    paths = []
    def walk_error(_):
        coverage["unreadable_directories"] += 1
    for folder in roots:
        for base, dirs, files in os.walk(folder, followlinks=False, onerror=walk_error):
            safe_dirs = [name for name in dirs if not (Path(base) / name).is_symlink()]
            coverage["skipped_links"] += len(dirs) - len(safe_dirs)
            dirs[:] = safe_dirs
            for name in files:
                if not name.endswith(".jsonl"):
                    continue
                path = Path(base) / name
                try:
                    info = path.lstat()
                    if not stat.S_ISREG(info.st_mode):
                        coverage["skipped_links_or_special_files"] += 1
                        continue
                    paths.append((info.st_mtime_ns, path))
                except OSError:
                    coverage["unreadable_files"] += 1
    coverage["discovered_files"] = len(paths)
    coverage["file_limit_excluded"] = max(0, len(paths) - max_files)
    sessions = []
    seen = set()
    for _, path in sorted(paths, key=lambda pair: (-pair[0], str(pair[1])))[:max_files]:
        coverage["scanned_files"] += 1
        try:
            session = read_session(path, root, start, end, tz, project, coverage)
        except (OSError, ValueError):
            coverage["unreadable_files"] += 1
            continue
        if session is None:
            continue
        if session["id"] in seen:
            coverage["duplicate_session_files"] += 1
            continue
        seen.add(session["id"])
        sessions.append(session)
    labels = {}
    basenames = Counter(Path(s["cwd"]).name for s in {s["cwd"]: s for s in sessions}.values())
    for session in sessions:
        cwd = session["cwd"]
        name = Path(cwd).name or "unknown"
        labels[cwd] = name if basenames[name] == 1 else name + " · " + hashlib.sha256(cwd.encode()).hexdigest()[:6]
    activity, evidence, index = {}, [], []
    for session in sessions:
        label, sid = labels[session["cwd"]], session["id"]
        for event in session["events"]:
            key = event["date"], label
            if key not in activity:
                activity[key] = {"date": key[0], "project": label, "sessions": set(), "requests": 0, "tools": 0, "errors": 0, "tool_names": Counter(), "commands": Counter(), "skills": Counter(), "tokens": empty_totals()}
            row = activity[key]
            row["sessions"].add(sid)
            if event["kind"] == "request":
                row["requests"] += 1
                match = re.match(r"^\s*\$([a-z][a-z0-9-]*)\b", event["text"])
                if match:
                    row["skills"][match.group(1)] += 1
            elif event["kind"] == "tool":
                row["tools"] += 1
                row["tool_names"][event["text"]] += 1
                if event.get("command"):
                    row["commands"][event["command"]] += 1
            elif event["kind"] == "tokens":
                add_tokens(row["tokens"], event["tokens"], sid)
            elif event["kind"] == "error":
                row["errors"] += 1
        candidates = [e for e in session["events"] if e["kind"] == "request"]
        # Evenly spaced request samples retain the start and end without dumping
        # every message; errors and command examples are sampled separately.
        sampled = [candidates[round(i * (len(candidates) - 1) / 5)] for i in range(6)] if len(candidates) > 6 else candidates
        sampled += [e for e in session["events"] if e["kind"] == "error"][:3]
        sampled += [e for e in session["events"] if e.get("command")][:3]
        refs = []
        for event in sorted(sampled, key=lambda item: item["line"]):
            ref = sid + ":L" + str(event["line"])
            refs.append(ref)
            evidence.append({"id": ref, "session": sid, "line": event["line"], "date": event["date"], "project": label, "kind": event["kind"], "text": excerpt(event.get("command") or event["text"])})
        index.append({"id": sid, "project": label, "cwd": session["cwd"], "source": session["source"], "evidence": refs})
    rows = sorted(activity.values(), key=lambda row: (row["date"], row["project"]))
    for row in rows:
        row["sessions"] = sorted(row["sessions"])
    incomplete = any(coverage[key] for key in GAPS)
    status = ("PARTIAL" if incomplete else "COLLECTED") if sessions else ("BLOCKED" if incomplete else "NO-DATA")
    return {"schema_version": 1, "host": "codex", "status": status, "generated_at": datetime.now(timezone.utc).isoformat(), "period": {"since": start.isoformat(), "until": end.isoformat(), "timezone": str(tz)}, "scope": "所选项目" if project else "本机全部项目", "coverage": dict(coverage), "sessions": index, "activity": rows, "evidence": evidence, "token_usage": dict(summarize(rows), scope="main_sessions")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    period = parser.add_mutually_exclusive_group()
    period.add_argument("--days", type=int)
    period.add_argument("--since", type=date.fromisoformat)
    parser.add_argument("--until", type=date.fromisoformat)
    parser.add_argument("--timezone", help="IANA zone, e.g. Asia/Shanghai; defaults to local time")
    parser.add_argument("--project")
    parser.add_argument("--output", help="explicit usage.json path; default: a new ${TREEFOLK_HOME:-~/.treefolk}/insights/<timestamp>/ directory")
    args = parser.parse_args()
    try:
        tz = ZoneInfo(args.timezone) if args.timezone else datetime.now().astimezone().tzinfo
        end = args.until or datetime.now(tz).date()
        days = args.days if args.days is not None else 90
        if days < 1:
            raise ValueError("--days must be positive")
        start = args.since or end - timedelta(days=days - 1)
        if start > end:
            raise ValueError("--since must not be later than --until")
        project = str(Path(args.project).expanduser().resolve()) if args.project else None
        result = collect(args.source, start, end, tz, project)
        output = Path(args.output).expanduser().absolute() if args.output else create_report_dir() / "usage.json"
        result.update(load_context(report_root(), output.parent, project, result["sessions"]))
        new_file(output, json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": result["status"], "period": result["period"], "sessions": len(result["sessions"]), "requests": sum(row["requests"] for row in result["activity"]), "evidence_samples": len(result["evidence"]), "coverage": result["coverage"], "token_usage": result["token_usage"], "history_items": len(result["history"]["items"]), "output": str(output), "report_dir": str(output.parent)}, ensure_ascii=False))
    except (OSError, ValueError, OverflowError, ZoneInfoNotFoundError) as error:
        parser.exit(2, "collect: " + str(error) + "\n")


if __name__ == "__main__":
    main()
