#!/usr/bin/env python3
"""Combine measured usage and agent-authored analysis into a self-contained HTML report."""

import argparse
from datetime import date
import json
from pathlib import Path
from urllib.parse import urlsplit

from storage import new_file
from context import ID, effective_knowledge, history_view, require, source, text_fields
from feedback import advice_id, checkbox_item, known_ids, shown_features, shown_findings
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
        require(feature["availability"] in {"local", "official", "reference", "unverified"}, "invalid feature availability")
        date.fromisoformat(feature["checked_at"])
        require(bool(feature.get("refs")) and set(feature["refs"]) <= refs, "feature has missing or unknown evidence")
        source(feature["source"])
    docs = effective_knowledge(usage.get("knowledge", []), analysis)
    doc_index = {item["id"]: item for item in docs}
    history = history_view(usage, analysis)
    for item in history:
        text_fields(item, ["title", "action", "first_seen", "last_seen"])
        require(date.fromisoformat(item["first_seen"]) <= date.fromisoformat(item["last_seen"]), "invalid history dates")
        for src in item["sources"]:
            require(src.get("origin") in {"report", "user_confirmation"}, "invalid history origin")
            date.fromisoformat(src["date"])
            if src.get("url"):
                url = urlsplit(src["url"])
                require(not url.scheme and not url.netloc and not url.query and not url.fragment and not url.path.startswith("/") and url.path.endswith("/report.html") and "\\" not in url.path, "history links must be relative report paths")
            else:
                require(src["origin"] == "user_confirmation", "missing original report link")
    if "history" in usage:
        prior_topics = {item["topic_id"] for item in history}
        prior_actions = {item["id"] for item in usage["history"].get("items", [])}
        for item in analysis.get("findings", []) + analysis.get("features", []):
            text_fields(item, ["topic_id"])
            require(bool(ID.fullmatch(item["topic_id"])), "invalid advice topic")
            action = item.get("action", item.get("command", ""))
            if item["topic_id"] in prior_topics or advice_id(action) in prior_actions:
                text_fields(item, ["new_detail"])
        for feature in analysis.get("features", []):
            text_fields(feature, ["when", "benefit"])
            doc_refs = feature.get("knowledge_refs", [])
            for ident in doc_refs:
                require(ident in doc_index, "unknown documentation reference")
            if doc_refs:
                require(any(feature["source"].get("url") == doc_index[ident]["source"]["url"] and feature["checked_at"] == doc_index[ident]["source_date"] for ident in doc_refs), "feature must retain the reference date and source")
    require(all(isinstance(item, str) for item in analysis.get("limitations", [])), "limitations must be text")


def render(usage, analysis):
    validate(usage, analysis)
    # Keep private source paths out of the webpage. It retains session IDs and
    # line references; the locally retained usage.json maps them to source files.
    public_usage = {key: value for key, value in usage.items() if key not in {"sessions", "history", "knowledge", "known_topics", "feedback"}}
    public_usage["sessions"] = [{"id": item["id"], "project": item["project"]} for item in usage["sessions"]]
    public_analysis = {key: value for key, value in analysis.items() if key not in {"history_groups", "confirmed_advice", "known_topics", "knowledge_updates"}}
    public_analysis["features"] = [dict(item, feedback=[checkbox_item(item)]) for item in shown_features(usage, analysis)]
    public_analysis["findings"] = [dict(item, feedback=[checkbox_item(item)]) for item in shown_findings(usage, analysis)]
    history = [{**{key: value for key, value in item.items() if key not in {"projects", "refs", "feedback_items"}}, "feedback": [checkbox_item(member) for member in item.get("feedback_items", [item])]} for item in history_view(usage, analysis)]
    docs = [{key: value for key, value in item.items() if key != "text"} for item in effective_knowledge(usage.get("knowledge", []), analysis)]
    feedback = {key: value for key, value in usage.get("feedback", {}).items() if key in {"status", "path", "store_id"}}
    feedback["known"] = sorted(known_ids(usage))
    data = json.dumps({"usage": public_usage, "analysis": public_analysis, "history": history, "history_coverage": usage.get("history", {}).get("coverage", {}), "knowledge": docs, "feedback": feedback}, ensure_ascii=False)
    data = data.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = (Path(__file__).resolve().parents[1] / "assets" / "report.html").read_text(encoding="utf-8")
    require(template.count("__INSIGHTS_DATA__") == 1, "invalid report template")
    script = (Path(__file__).resolve().parents[1] / "assets" / "feedback.js").read_text(encoding="utf-8")
    require(template.count("__INSIGHTS_FEEDBACK__") == 1, "invalid feedback template")
    return template.replace("__INSIGHTS_FEEDBACK__", script).replace("__INSIGHTS_DATA__", data)


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
