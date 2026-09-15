"""Read prior reports once for original advice and reusable documentation.

No network, prompt execution, adoption inference, or writes to old reports.
The documentation is reference material, never a fixed recommendation pool.
"""

import argparse
from collections import Counter
from datetime import date, datetime
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import quote, urlsplit

from feedback import advice_id, load_feedback, shown_features, shown_findings

MAX_REPORTS = 200
MAX_ITEMS = 200
MAX_JSON_BYTES = 16 * 1024 * 1024
ID = re.compile(r"[a-z0-9][a-z0-9-]{0,79}\Z")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def text_fields(item, fields):
    require(isinstance(item, dict), "expected an object")
    for key in fields:
        require(isinstance(item.get(key), str) and bool(item[key].strip()), "missing text: " + key)


def source(value):
    text_fields(value, ["title"])
    if not value.get("url"):
        return
    url = urlsplit(value["url"])
    official = url.hostname in {"openai.com", "developers.openai.com", "platform.openai.com", "learn.chatgpt.com", "help.openai.com"}
    official = official or (url.hostname == "github.com" and (url.path == "/openai/codex" or url.path.startswith("/openai/codex/")))
    require(url.scheme == "https" and official and not url.username and not url.password, "feature sources must be official HTTPS URLs")


def read_json(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_JSON_BYTES, "unsupported report file")
        return json.loads(stream.read(MAX_JSON_BYTES + 1))


def document(item):
    text_fields(item, ["id", "text", "source_date"])
    require(bool(ID.fullmatch(item["id"])) and len(item["text"]) <= 8000, "invalid reference document")
    date.fromisoformat(item["source_date"])
    source(item["source"])
    require(bool(item["source"].get("url")), "documentation needs an official source")
    quick = item.get("quick_reference", [])
    require(isinstance(quick, list) and len(quick) <= 20, "invalid quick reference")
    for row in quick:
        text_fields(row, ["host", "platform", "keys", "action", "when"])
        require(row["host"] in {"app", "cli"} and row["platform"] in {"all", "macos", "windows", "linux"}, "invalid shortcut scope")


def knowledge_updates(analysis):
    updates = analysis.get("knowledge_updates", [])
    require(isinstance(updates, list) and len(updates) <= 20, "invalid knowledge updates")
    if updates:
        latest = analysis.get("latest", {})
        require(latest.get("enabled") is True and latest.get("status") in {"checked", "partial"}, "offline or failed queries cannot refresh knowledge")
        urls = {s.get("url") for s in latest.get("sources", [])}
        for item in updates:
            document(item)
            require(item["source"]["url"] in urls and item["source_date"] == latest.get("checked_at"), "knowledge must reference this run's actual query")
    return updates


def bundled_knowledge():
    result = read_json(Path(__file__).resolve().parents[1] / "references" / "codex-reference.json")
    require(result.get("schema_version") == 1, "unsupported reference schema")
    for item in result["documents"]:
        document(item)
    return [dict(item, origin="bundled") for item in result["documents"]]


def effective_knowledge(base, analysis):
    result = {}
    for item in base:
        document(item)
        result[item["id"]] = item
    for item in knowledge_updates(analysis):
        previous = result.get(item["id"])
        require(not previous or item["source_date"] >= previous["source_date"], "cannot replace knowledge with an older snapshot")
        result[item["id"]] = dict(item, origin="current_query")
    return list(result.values())


def confirmed_items(analysis):
    result = []
    for item in analysis.get("confirmed_advice", []):
        text_fields(item, ["topic_id", "title", "action", "confirmed_at", "note"])
        require(bool(ID.fullmatch(item["topic_id"])), "invalid confirmed topic")
        date.fromisoformat(item["confirmed_at"])
        require(all(isinstance(p, str) and os.path.isabs(p) for p in item.get("projects", [])), "confirmed projects must be absolute paths")
        result.append(dict(item, id=advice_id(item["action"])))
    return result


def in_project(cwd, project):
    return isinstance(cwd, str) and os.path.isabs(cwd) and os.path.commonpath([os.path.normpath(cwd), project]) == project


def load_context(root, output_dir, project=None, current_sessions=(), max_reports=MAX_REPORTS):
    root, output_dir = Path(root), Path(output_dir)
    docs = {item["id"]: item for item in bundled_knowledge()}
    history, coverage = {}, Counter()
    if root.is_symlink():
        raise ValueError("report history root must not be a symlink")
    try:
        folders = sorted((p for p in root.iterdir() if p.is_dir() and not p.is_symlink() and p != output_dir), reverse=True)
    except FileNotFoundError:
        folders = []
    except OSError:
        folders = []
        coverage["unreadable_root"] += 1
    coverage["report_limit_excluded"] = max(0, len(folders) - max_reports)
    current_paths = {s["id"]: s.get("cwd") for s in current_sessions}
    versions = {key: (item["source_date"], "") for key, item in docs.items()}
    for folder in folders[:max_reports]:
        coverage["scanned_reports"] += 1
        try:
            usage = read_json(folder / "usage.json")
            if usage.get("demo"):
                coverage["demo_reports"] += 1
                continue
            analysis = read_json(folder / "analysis.json")
            require(not (folder / "report.html").is_symlink() and (folder / "report.html").is_file(), "missing report")
            require(usage.get("schema_version") == 1 and usage.get("host") == "codex" and usage.get("status") in {"COLLECTED", "PARTIAL"}, "invalid usage")
            text_fields(analysis, ["summary"])
            stamp = datetime.fromisoformat(usage["generated_at"].replace("Z", "+00:00")).date().isoformat()
            originals = [(item, "action", "report") for item in shown_findings(usage, analysis)]
            originals += [(item, "command", "report") for item in shown_features(usage, analysis)]
            originals += [(item, "action", "user_confirmation") for item in confirmed_items(analysis)]
            # Reuse only original query snapshots, never generated advice as docs.
            updates = knowledge_updates(analysis)
            session_paths = {s["id"]: s.get("cwd") or current_paths.get(s["id"]) for s in usage["sessions"]}
            refs = {e["id"]: session_paths.get(e["session"]) for e in usage["evidence"]}
        except FileNotFoundError:
            coverage["incomplete_reports"] += 1
            continue
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            coverage["invalid_reports"] += 1
            continue
        coverage["imported_reports"] += 1
        for item in updates:
            version = item["source_date"], usage["generated_at"]
            if version > versions.get(item["id"], ("", "")):
                docs[item["id"]] = dict(item, origin="prior_query", report_id=folder.name)
                versions[item["id"]] = version
        for item, action_key, origin in originals:
            try:
                text_fields(item, ["title", action_key])
                if origin == "report":
                    require(bool(item.get("refs")) and all(ref in refs for ref in item["refs"]), "invalid advice evidence")
                    paths = [refs[ref] for ref in item["refs"]]
                else:
                    paths = item.get("projects", [])
                if project and not any(in_project(p, project) for p in paths):
                    coverage["advice_outside_or_unknown_project"] += 1
                    continue
                ident = advice_id(item[action_key])
                day = item.get("confirmed_at", stamp) if origin == "user_confirmation" else stamp
                topic = item.get("topic_id", ident)
                require(isinstance(topic, str) and bool(ID.fullmatch(topic)), "invalid advice topic")
                entry = history.setdefault(ident, {"id": ident, "topic_id": topic, "title": item["title"][:160], "action": item[action_key][:500], "first_seen": day, "last_seen": day, "sources": []})
                entry["first_seen"] = min(entry["first_seen"], day)
                entry["last_seen"] = max(entry["last_seen"], day)
                src = {"report_id": folder.name, "date": day, "origin": origin, "url": quote(os.path.relpath(folder / "report.html", output_dir), safe="/.-_~")}
                if src not in entry["sources"]:
                    entry["sources"].append(src)
            except (ValueError, KeyError, TypeError):
                coverage["invalid_advice"] += 1
    items = sorted(history.values(), key=lambda item: (item["last_seen"], item["id"]), reverse=True)
    coverage["advice_limit_excluded"] = max(0, len(items) - MAX_ITEMS)
    return {"history": {"items": items[:MAX_ITEMS], "coverage": dict(coverage)}, "knowledge": list(docs.values()), "feedback": load_feedback(root)}


def history_view(usage, analysis):
    items = {item["id"]: item for item in usage.get("history", {}).get("items", [])}
    for item in confirmed_items(analysis):
        day = item["confirmed_at"]
        src = {"date": day, "origin": "user_confirmation", "note": item["note"], "url": None}
        if item["id"] in items:
            old = items[item["id"]]
            items[item["id"]] = dict(old, sources=[*old["sources"], src], first_seen=min(old["first_seen"], day), last_seen=max(old["last_seen"], day))
        else:
            items[item["id"]] = {**item, "first_seen": day, "last_seen": day, "sources": [src]}
    grouped, used = [], set()
    for group in analysis.get("history_groups", []):
        text_fields(group, ["topic_id", "title", "action"])
        require(bool(ID.fullmatch(group["topic_id"])), "invalid history topic")
        ids = group.get("items", [])
        require(bool(ids) and len(set(ids)) == len(ids) and set(ids) <= items.keys() and not used.intersection(ids), "invalid history group references")
        members = [items[ident] for ident in ids]
        grouped.append({**group, "first_seen": min(m["first_seen"] for m in members), "last_seen": max(m["last_seen"] for m in members), "sources": [s for m in members for s in m["sources"]], "feedback_items": [{k: m[k] for k in ("id", "title", "action")} for m in members]})
        used.update(ids)
    return grouped + [item for ident, item in items.items() if ident not in used]


def main():
    parser = argparse.ArgumentParser(description="Read a compact reference index or selected local documents; never fetches the network.")
    parser.add_argument("--usage", required=True)
    parser.add_argument("--ids", nargs="*", help="omit for index; supply arbitrary document IDs to read their text")
    parser.add_argument("--history", action="store_true", help="show a bounded page of original advice and known topics")
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    usage = read_json(args.usage)
    docs = usage.get("knowledge", [])
    if args.history:
        if args.offset < 0:
            parser.error("--offset must be nonnegative")
        items = usage.get("history", {}).get("items", [])
        known = [i for i in usage.get("feedback", {}).get("entries", []) if i["known"]]
        result = {"total": len(items), "offset": args.offset, "items": [{"id": i["id"], "topic_id": i["topic_id"], "title": i["title"], "action": i["action"][:180]} for i in items[args.offset:args.offset + 20]], "known_total": len(known), "known_advice": [{"id": i["id"], "label": i["label"][:240]} for i in known[args.offset:args.offset + 20]], "feedback_status": usage.get("feedback", {}).get("status", "missing")}
    else:
        result = [d for d in docs if d["id"] in args.ids] if args.ids is not None else [{"id": d["id"], "title": d["source"]["title"], "source_date": d["source_date"]} for d in docs]
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
