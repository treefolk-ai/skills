#!/usr/bin/env python3
"""Combine measured usage and agent-authored analysis into a self-contained HTML report."""

import argparse
from datetime import date
import json
from pathlib import Path

from storage import new_file
from context import ID, advice_id, effective_knowledge, require, source, text_fields
from tokens import FIELDS


def validate_tokens(item, sessions):
    require(isinstance(item, dict), "invalid token data")
    for field in FIELDS:
        value = item.get(field)
        require(value is None or (type(value) is int and value >= 0), "invalid token count")
    require(all(type(n) is int and n >= 0 for n in item["coverage"].values()), "invalid token coverage")
    require(set(item["sessions"]) <= sessions, "unknown token session")
    incoming, outgoing, cached, eligible, used = (item.get(k) for k in FIELDS)
    require((incoming is None) == (outgoing is None), "incomplete input/output pair")
    require((cached is None) == (eligible is None) == (used is None), "incomplete cache pair")
    if cached is not None:
        require(incoming is not None and cached <= eligible <= incoming and eligible - cached <= used <= eligible - cached + outgoing, "inconsistent token counts")


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
        if "tokens" in row:
            validate_tokens(row["tokens"], set(row["sessions"]))
    text_fields(analysis, ["summary"])
    reviewed = analysis.get("reviewed_sessions")
    require(isinstance(reviewed, list) and set(reviewed) <= sessions, "reviewed_sessions must reference collected sessions")
    require(len(reviewed) == len(set(reviewed)), "duplicate reviewed sessions")
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
    items = analysis.get("suggestions")
    require(isinstance(items, list) and len(items) <= 3, "expected at most three suggestions")
    docs = {d["id"]: d for d in effective_knowledge(usage.get("knowledge", []), analysis)}
    history = usage.get("history", {}).get("items", [])
    prior_topics = {i["topic_id"] for i in history}
    prior_actions = {i["id"] for i in history}
    actions = set()
    for item in items:
        text_fields(item, ["topic_id", "title", "why", "action"])
        require(bool(ID.fullmatch(item["topic_id"])), "invalid advice topic")
        require(bool(item.get("refs")) and set(item["refs"]) <= refs, "suggestion has missing or unknown evidence")
        ident = advice_id(item["action"])
        require(ident not in actions, "duplicate suggestion")
        actions.add(ident)
        if item["topic_id"] in prior_topics or ident in prior_actions:
            text_fields(item, ["new_detail"])
        doc_refs = item.get("knowledge_refs", [])
        require(isinstance(doc_refs, list) and all(isinstance(i, str) and i in docs for i in doc_refs), "unknown documentation reference")
        if "try" in item:
            text_fields(item["try"], ["where", "text", "expect"])
    require(all(isinstance(item, str) for item in analysis.get("limitations", [])), "limitations must be text")


def render(usage, analysis):
    validate(usage, analysis)
    public_usage = {key: value for key, value in usage.items() if key in {"schema_version", "host", "status", "generated_at", "period", "scope", "coverage", "activity", "evidence", "token_usage", "demo"}}
    public_usage["sessions"] = [{"id": item["id"], "project": item["project"]} for item in usage["sessions"]]
    public_analysis = {key: value for key, value in analysis.items() if key in {"summary", "reviewed_sessions", "suggestions", "latest", "limitations"}}
    used_docs = {ident for item in analysis["suggestions"] for ident in item.get("knowledge_refs", [])}
    docs = [{key: d[key] for key in ("id", "source", "source_date")} for d in effective_knowledge(usage.get("knowledge", []), analysis) if d["id"] in used_docs]
    data = json.dumps({"usage": public_usage, "analysis": public_analysis, "knowledge": docs}, ensure_ascii=False)
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
