#!/usr/bin/env python3
"""Combine measured usage and agent-authored analysis into a self-contained HTML report."""

import argparse
from datetime import date
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

from storage import new_file


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text_fields(item, fields):
    require(isinstance(item, dict), "expected an object")
    for field in fields:
        require(isinstance(item.get(field), str) and bool(item[field].strip()), "missing text: " + field)


def source(value):
    text_fields(value, ["title"])
    if not value.get("url"):
        return
    url = urlsplit(value["url"])
    official = url.hostname in {"openai.com", "developers.openai.com", "platform.openai.com", "learn.chatgpt.com", "help.openai.com"}
    official = official or (url.hostname == "github.com" and (url.path == "/openai/codex" or url.path.startswith("/openai/codex/")))
    require(url.scheme == "https" and official and not url.username and not url.password, "feature sources must be official HTTPS URLs")


def validate(usage, analysis):
    require(usage.get("schema_version") == 1, "unsupported usage schema")
    require(usage.get("host") == "codex", "only Codex usage is currently supported")
    start, end = (date.fromisoformat(usage["period"][key]) for key in ("since", "until"))
    require(start <= end, "invalid usage period")
    require(bool(usage.get("sessions")), "no sessions: report NO-DATA instead of generating recommendations")
    sessions = {item["id"] for item in usage["sessions"]}
    refs = {item["id"] for item in usage["evidence"]}
    require(len(refs) == len(usage["evidence"]), "duplicate evidence IDs")
    for item in usage["evidence"]:
        require(item["session"] in sessions, "evidence points to an unknown session")
        require(start <= date.fromisoformat(item["date"]) <= end, "evidence outside period")
    for row in usage["activity"]:
        require(start <= date.fromisoformat(row["date"]) <= end, "activity outside period")
        require(set(row["sessions"]) <= sessions, "activity points to an unknown session")
        for field in ("requests", "tools", "errors"):
            require(type(row[field]) is int and row[field] >= 0, "invalid activity count")
        for field in ("commands", "skills", "tool_names"):
            require(isinstance(row[field], dict) and all(type(n) is int and n >= 0 for n in row[field].values()), "invalid distribution")
    text_fields(analysis, ["summary"])
    reviewed = analysis.get("reviewed_sessions")
    require(isinstance(reviewed, list) and set(reviewed) <= sessions, "reviewed_sessions must reference collected sessions")
    require(len(reviewed) == len(set(reviewed)), "duplicate reviewed sessions")
    for finding in analysis.get("findings", []):
        text_fields(finding, ["title", "observation", "interpretation", "action", "check", "confidence"])
        require(finding["confidence"] in {"high", "medium", "low"}, "invalid confidence")
        require(bool(finding.get("refs")) and set(finding["refs"]) <= refs, "finding has missing or unknown evidence")
    latest = analysis["latest"]
    require(type(latest.get("enabled")) is bool, "latest.enabled must be boolean")
    require(latest.get("status") in {"checked", "partial", "unavailable", "off"}, "invalid latest status")
    require(latest["enabled"] == (latest["status"] != "off"), "latest switch and status disagree")
    if latest["status"] in {"checked", "partial"}:
        date.fromisoformat(latest["checked_at"])
        require(bool(latest.get("sources")), "queried features require actual sources")
        require(all(item.get("url") for item in latest["sources"]), "queried features require official URLs")
    else:
        require(latest.get("checked_at") is None and not latest.get("sources"), "an unperformed query cannot have a checked date or sources")
    for item in latest.get("sources", []):
        source(item)
    for feature in analysis.get("features", []):
        text_fields(feature, ["title", "why", "command", "availability", "version", "checked_at"])
        require(feature["availability"] in {"local", "official", "unverified"}, "invalid feature availability")
        date.fromisoformat(feature["checked_at"])
        require(bool(feature.get("refs")) and set(feature["refs"]) <= refs, "feature has missing or unknown evidence")
        source(feature["source"])
    require(all(isinstance(item, str) for item in analysis.get("limitations", [])), "limitations must be text")


def render(usage, analysis):
    validate(usage, analysis)
    # Keep private source paths out of the webpage. It retains session IDs and
    # line references; the locally retained usage.json maps them to source files.
    public_usage = {key: value for key, value in usage.items() if key != "sessions"}
    public_usage["sessions"] = [{"id": item["id"], "project": item["project"]} for item in usage["sessions"]]
    data = json.dumps({"usage": public_usage, "analysis": analysis}, ensure_ascii=False)
    data = data.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = (Path(__file__).resolve().parents[1] / "assets" / "report.html").read_text(encoding="utf-8")
    require(template.count("__INSIGHTS_DATA__") == 1, "invalid report template")
    return template.replace("__INSIGHTS_DATA__", data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usage", required=True)
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--output", help="explicit HTML path; default: report.html beside usage.json")
    args = parser.parse_args()
    try:
        usage_path = Path(args.usage).expanduser().absolute()
        usage = json.loads(usage_path.read_text(encoding="utf-8"))
        analysis = json.loads(Path(args.analysis).expanduser().read_text(encoding="utf-8"))
        output = Path(args.output).expanduser().absolute() if args.output else usage_path.with_name("report.html")
        new_file(output, render(usage, analysis))
        print("Rendered: " + str(output))
        print("Report directory: " + str(output.parent))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, "render: " + str(error) + "\n")


if __name__ == "__main__":
    main()
