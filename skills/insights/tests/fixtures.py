"""Build a synthetic report inside an explicitly supplied test directory."""

from datetime import date, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from collect import collect
from render import render
from storage import new_file
from context import advice_id, bundled_knowledge


def make_report(folder):
    folder = Path(folder).expanduser().absolute()
    folder.mkdir(mode=0o700)
    source = folder / "source"
    (source / "sessions").mkdir(parents=True)
    end = date(2026, 9, 15)
    projects = ["music-notes", "garden", "workbench"]
    prompts = [
        ["继续上次的编辑器任务，我找不到之前的会话了。", "我又切换目录找了一遍，上次的记录在哪里？", "找到后继续同一个任务，保留已经确认的约束。"],
        ["调整首页的层级，使用项目现有依赖。", "先不要增加依赖，保留现在的实现方案。", "页面效果可以了；以后开始前先核对这条约束。"],
        ["$build 给设置页增加筛选，刷新后保留选择。", "请用实际页面验证筛选，同时检查窄屏。", "交互符合预期，保留这种实际查看结果的方式。"],
    ]
    for i in range(15):
        day = end - timedelta(days=84 - 6 * i)
        sid = "demo-session-" + str(i + 1).zfill(2)
        project = projects[i % 3]
        stamp = day.isoformat() + "T10:00:00+08:00"
        records = [{"timestamp": stamp, "type": "session_meta", "payload": {"id": sid, "cwd": "/demo/" + project, "source": "cli"}}]
        incoming = outgoing = cached = 0
        for j, prompt in enumerate(prompts[i % 3]):
            records.append({"timestamp": stamp, "type": "event_msg", "payload": {"type": "user_message", "message": prompt}})
            for k in range(j + 1):
                records.append({"timestamp": stamp, "type": "response_item", "payload": {"type": "function_call", "name": "functions.exec_command", "call_id": sid + "-" + str(j) + "-" + str(k), "arguments": json.dumps({"cmd": ["git status --short", "rg --files", "pnpm test"][j]})}})
            delta = {"input_tokens": 23000 + 1100 * i + 2000 * j, "output_tokens": 350 + 35 * i, "cached_input_tokens": 18000 + 1000 * i}
            incoming += delta["input_tokens"]
            outgoing += delta["output_tokens"]
            cached += delta["cached_input_tokens"]
            total = {"input_tokens": incoming, "output_tokens": outgoing, "cached_input_tokens": cached, "reasoning_output_tokens": 100}
            if i == 13:
                total.pop("cached_input_tokens")
                delta.pop("cached_input_tokens")
            event = {"timestamp": stamp, "type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": total, "last_token_usage": delta}}}
            records.append(event)
            records.append(event)  # Repeated status snapshots must not double count.
        new_file(source / "sessions" / (sid + ".jsonl"), "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n")
    usage = collect(source, end - timedelta(days=89), end, ZoneInfo("Asia/Shanghai"))
    usage["demo"] = True
    usage["knowledge"] = bundled_knowledge()
    usage["history"] = {"items": [{"id": advice_id("先确认目标与计划"), "topic_id": "plan-first", "title": "先确认计划", "action": "先确认目标与计划", "last_seen": "2026-08-10", "report_id": "synthetic-prior"}], "coverage": {}}
    request_refs = {}
    for item in usage["evidence"]:
        if item["kind"] == "request":
            request_refs.setdefault(item["project"], []).append(item["id"])
    analysis = {
        "summary": "在这组示例中，你已经习惯亲自查看 AI 的结果。更值得调整的是找回工作现场、核对已有约束，让下一次开始得更顺畅。",
        "reviewed_sessions": [s["id"] for s in usage["sessions"]],
        "suggestions": [
            {"topic_id": "recover-original-prompt", "title": "忘了原话时，搜索自己写过的提示", "why": "合成记录里的 music-notes 请求多次提到寻找原话；提示历史可能提供更短的检索路径。", "action": "在 CLI 需要找回写过的需求时，按 Ctrl+R 搜索提示历史，Enter 使用匹配项，Esc 取消。这不会恢复整段会话。", "knowledge_refs": ["cli-interaction"], "refs": request_refs["music-notes"][:2]},
            {"topic_id": "restate-constraints", "title": "把反复纠正的限制放到开始时", "why": "garden 的合成请求已经限制新增依赖，之后仍反复提醒；可能是执行约束的方式需要调整。", "action": "下一次有明确限制的任务开始时，让 AI 先找出影响实现的关键约束。", "try": {"where": "开始一项有明确限制的开发任务时，粘贴到已有需求的 Codex 对话中。", "text": "开始前，先列出影响这次实现的三条硬约束，并指出需求中是否有冲突。没有冲突就沿用这些约束继续。", "expect": "先看到简短的约束清单，再据此推进实现。"}, "refs": request_refs["garden"][:2]},
            {"topic_id": "retain-live-feedback", "title": "保留亲自看页面的习惯", "why": "workbench 的合成会话在筛选和窄屏检查后给出了具体反馈；这支持保留实际体验环节。", "action": "以后验收交互改动时继续亲自查看页面，并说清哪些场景已经看过。旧任务可能已结束，现在无需重新验收。", "refs": request_refs["workbench"][1:3]},
        ],
        "latest": {"enabled": False, "status": "off", "checked_at": None, "sources": [], "note": "使用本地带日期的资料摘要，本次没有联网查询。"},
        "limitations": ["全部数据和分析均为合成示例，不代表真实个人习惯。", "记录频次不等于人工操作次数；无法辨认的分叉历史可能重复。"],
    }
    new_file(folder / "usage.json", json.dumps(usage, ensure_ascii=False, indent=2) + "\n")
    new_file(folder / "analysis.json", json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")
    new_file(folder / "report.html", render(usage, analysis))
    return usage, analysis
