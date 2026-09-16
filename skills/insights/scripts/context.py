"""Read prior advice for novelty and reuse dated official documentation, without writes."""

import argparse
from collections import Counter
from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

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


def advice_id(action):
    return "advice-" + hashlib.sha256(" ".join(action.split()).casefold().encode()).hexdigest()[:16]


def source(value):
    text_fields(value, ["title", "url"])
    url = urlsplit(value["url"])
    official = url.hostname in {"openai.com", "developers.openai.com", "platform.openai.com", "learn.chatgpt.com", "help.openai.com"}
    official = official or (url.hostname == "github.com" and (url.path == "/openai/codex" or url.path.startswith("/openai/codex/")))
    require(url.scheme == "https" and official and not url.username and not url.password, "sources must be official HTTPS URLs")


def read_json(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_JSON_BYTES, "unsupported report file")
        return json.loads(stream.read(MAX_JSON_BYTES + 1))


def document(item):
    text_fields(item, ["id", "text", "source_date"])
    require(bool(ID.fullmatch(item["id"])) and len(item["text"]) <= 8000, "invalid reference document")
    date.fromisoformat(item["source_date"])
    source(item["source"])


def knowledge_updates(analysis):
    updates = analysis.get("knowledge_updates", [])
    require(isinstance(updates, list) and len(updates) <= 20, "invalid knowledge updates")
    if updates:
        latest = analysis.get("latest", {})
        require(latest.get("enabled") is True and latest.get("status") in {"checked", "partial"}, "an unperformed query cannot save fresh knowledge")
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


def original_advice(usage, analysis):
    if "suggestions" in analysis:
        items = analysis["suggestions"]
        require(isinstance(items, list) and len(items) <= 3, "expected at most three suggestions")
        return items
    # Reconstruct only what legacy reports displayed, using their saved snapshot.
    # Never read known.md or import copied history as new advice.
    findings, features = analysis.get("findings", []), analysis.get("features", [])
    if usage.get("suggestion_selection") == "random-v1":
        known = {i["id"] for i in usage.get("feedback", {}).get("entries", []) if i["known"]}
        findings = [i for i in findings if advice_id(i["action"]) not in known]
        unique = {advice_id(i["command"]): i for i in reversed(features) if advice_id(i["command"]) not in known}
        ids = sorted(unique, key=lambda ident: hashlib.sha256((usage["generated_at"] + ident).encode()).digest())
        features = [unique[ident] for ident in ids[:3]]
    return findings + [dict(i, action=i["command"]) for i in features]


def load_context(root, output_dir, project=None, current_sessions=(), max_reports=MAX_REPORTS):
    root, output_dir = Path(root), Path(output_dir)
    docs = {item["id"]: item for item in bundled_knowledge()}
    history, coverage = {}, Counter()
    require(not root.is_symlink(), "report history root must not be a symlink")
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
            stamp = datetime.fromisoformat(usage["generated_at"].replace("Z", "+00:00")).date().isoformat()
            originals = original_advice(usage, analysis)
            updates = knowledge_updates(analysis)
            paths = {s["id"]: s.get("cwd") or current_paths.get(s["id"]) for s in usage["sessions"]}
            refs = {e["id"]: paths.get(e["session"]) for e in usage["evidence"]}
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
        for item in originals:
            try:
                text_fields(item, ["title", "action"])
                require(bool(item.get("refs")) and all(ref in refs for ref in item["refs"]), "invalid advice evidence")
                if project and not any(isinstance(refs[r], str) and os.path.isabs(refs[r]) and os.path.commonpath([os.path.normpath(refs[r]), project]) == project for r in item["refs"]):
                    coverage["advice_outside_or_unknown_project"] += 1
                    continue
                ident = advice_id(item["action"])
                topic = item.get("topic_id", ident)
                require(bool(ID.fullmatch(topic)), "invalid advice topic")
                if ident not in history or stamp > history[ident]["last_seen"]:
                    history[ident] = {"id": ident, "topic_id": topic, "title": item["title"][:160], "action": item["action"][:500], "last_seen": stamp, "report_id": folder.name}
            except (ValueError, KeyError, TypeError):
                coverage["invalid_advice"] += 1
    items = sorted(history.values(), key=lambda i: (i["last_seen"], i["id"]), reverse=True)
    coverage["advice_limit_excluded"] = max(0, len(items) - MAX_ITEMS)
    return {"history": {"items": items[:MAX_ITEMS], "coverage": dict(coverage)}, "knowledge": list(docs.values())}


def main():
    parser = argparse.ArgumentParser(description="Read prior advice or dated references; no network or writes.")
    parser.add_argument("--usage", required=True)
    parser.add_argument("--ids", nargs="*", help="document IDs; omit for the reference index")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    usage = read_json(args.usage)
    if args.offset < 0:
        parser.error("--offset must be nonnegative")
    if args.history:
        items = usage.get("history", {}).get("items", [])
        result = {"total": len(items), "offset": args.offset, "items": items[args.offset:args.offset + 20]}
    else:
        docs = usage.get("knowledge", [])
        result = [d for d in docs if d["id"] in args.ids] if args.ids is not None else [{"id": d["id"], "title": d["source"]["title"], "source_date": d["source_date"]} for d in docs]
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
