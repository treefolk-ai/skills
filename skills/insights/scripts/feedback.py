"""One human-editable checkbox file; only the browser changes existing choices."""

import hashlib
import os
from pathlib import Path
import re
import stat
import uuid

from storage import new_file

MAX_BYTES = 512 * 1024
HEADER = re.compile(r"<!-- treefolk-insights-known:v1:([a-f0-9]{32}) -->\Z")
ROW = re.compile(r"- \[([ xX])\] (.+) <!-- insights:(advice-[a-f0-9]{16}) -->\Z")


def advice_id(action):
    normalized = " ".join(action.casefold().split())
    return "advice-" + hashlib.sha256(normalized.encode()).hexdigest()[:16]


def parse_feedback(text):
    lines = text.splitlines()
    header = HEADER.fullmatch(lines[0]) if lines else None
    if not header or len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("invalid insights checkbox file")
    entries, seen = [], set()
    for line in lines[1:]:
        match = ROW.fullmatch(line)
        if not match:
            if "<!-- insights:" in line:
                raise ValueError("invalid checkbox row")
            continue
        checked, label, ident = match.groups()
        if ident in seen:
            raise ValueError("duplicate checkbox ID")
        seen.add(ident)
        entries.append({"id": ident, "label": label, "known": checked.lower() == "x"})
    return {"store_id": header[1], "entries": entries}


def load_feedback(root, create=False):
    path = Path(root) / "known.md"
    try:
        if Path(root).is_symlink():
            raise ValueError("checkbox directory must not be a symlink")
        if create:
            try:
                new_file(path, "<!-- treefolk-insights-known:v1:" + uuid.uuid4().hex + " -->\n"
                         "# 我已经知道的用法\n\n勾选表示已知；取消勾选可恢复推荐。请保留条目后的标识。\n")
            except FileExistsError:
                pass
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                raise ValueError("unsupported checkbox file")
            state = parse_feedback(stream.read(MAX_BYTES + 1).decode("utf-8"))
        return {"status": "ready", "path": str(path.absolute()), **state}
    except FileNotFoundError:
        return {"status": "missing", "path": str(path.absolute()), "entries": []}
    except (OSError, ValueError) as error:
        return {"status": "unavailable", "path": str(path.absolute()), "entries": [], "note": str(error)}


def known_ids(usage):
    return {item["id"] for item in usage.get("feedback", {}).get("entries", []) if item["known"]}


def shown_findings(usage, analysis):
    items = analysis.get("findings", [])
    if usage.get("suggestion_selection") != "random-v1":
        return items
    known = known_ids(usage)
    return [item for item in items if advice_id(item["action"]) not in known]


def shown_features(usage, analysis):
    candidates = analysis.get("features", [])
    if usage.get("suggestion_selection") != "random-v1":
        return candidates
    # Stable within one report, shuffled afresh for each generation. Reusing
    # the stored snapshot also reconstructs exactly what an old report showed.
    known, unique = known_ids(usage), {}
    for item in candidates:
        ident = advice_id(item["command"])
        if ident not in known:
            unique.setdefault(ident, item)
    seed = usage["generated_at"]
    ids = sorted(unique, key=lambda ident: hashlib.sha256((seed + ident).encode()).digest())
    return [unique[ident] for ident in ids[:3]]


def checkbox_item(item):
    action = item.get("action", item.get("command", ""))
    label = " ".join((item["title"] + "：" + action).split())[:1800]
    label = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return {"id": item.get("id") or advice_id(action), "label": label}
