"""Build a synthetic report inside an explicitly supplied test directory."""

from datetime import date, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from collect import collect
from render import render
from storage import new_file
from context import bundled_knowledge
from feedback import advice_id, load_feedback


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
    usage["feedback"] = load_feedback(folder, create=True)
    usage["suggestion_selection"] = "random-v1"
    usage["knowledge"] = bundled_knowledge()
    usage["history"] = {"items": [], "coverage": {}}
    for n, (topic, title, action) in enumerate([
        ("plan-first", "先确认计划", "先确认目标与计划，再开始实现。"),
        ("plan-first", "需求不清楚时先讨论", "在目标不清楚时先整理计划中的待决定项。"),
        ("worktree-isolation", "并行任务使用 worktree", "在独立 worktree 中推进另一个实现任务。"),
    ]):
        old = folder / ("previous-" + str(n + 1))
        old.mkdir()
        day = "2026-08-" + str(10 + n)
        new_file(old / "report.html", '<!doctype html><meta charset="utf-8"><title>合成旧报告</title><h1>合成旧报告</h1><h2>' + title + '</h2><p>' + action + '</p><p>' + day + ' · 演示来源，不代表个人记录。</p>')
        usage["history"]["items"].append({"id": advice_id(action), "topic_id": topic, "title": title, "action": action, "first_seen": day, "last_seen": day, "sources": [{"report_id": old.name, "date": day, "origin": "report", "url": old.name + "/report.html"}]})
    request_refs = {}
    for item in usage["evidence"]:
        if item["kind"] == "request":
            request_refs.setdefault(item["project"], []).append(item["id"])
    analysis = {
        "summary": "在这组示例中，你已经习惯亲自查看 AI 的结果。更值得调整的是找回工作现场、核对已有约束，让下一次开始得更顺畅。",
        "reviewed_sessions": [s["id"] for s in usage["sessions"]],
        "findings": [
            {"title": "让未完的任务更容易接上", "observation": "多个 music-notes 会话里，继续任务之前先花了一轮对话寻找旧会话。", "interpretation": "可能是跨项目会话的入口不明显；记录不能证明你不了解恢复功能。", "action": "开始前先查找并恢复原会话，让已经确认的上下文跟着任务一起回来。", "check": "下次继续任务时，观察是否还需要重复解释已经确认的约束。", "confidence": "medium", "refs": request_refs["music-notes"][:2] + request_refs["music-notes"][3:4]},
            {"title": "把约束核对放在开始时", "observation": "garden 的请求已经写明使用现有依赖，后续仍反复提醒不要增加依赖。", "interpretation": "这是 AI 执行约束时的摩擦；更长的提示未必有帮助。", "action": "让 AI 开始前简短复述这次最重要的约束，再据此选择实现方案。", "check": "下一项类似任务里，检查是否减少了同一条约束的重复纠正。", "confidence": "medium", "refs": request_refs["garden"][:2] + request_refs["garden"][3:4]},
            {"title": "保留实际查看页面的习惯", "observation": "workbench 的会话中，页面筛选和窄屏检查之后有明确的使用反馈。", "interpretation": "这些记录支持继续保留实际体验环节；它们不足以证明所有场景都通过。", "action": "完成交互改动后继续查看真实页面，用具体反馈决定是否验收。", "check": "同时记录已查看的场景和仍未查看的场景。", "confidence": "high", "refs": request_refs["workbench"][1:3]},
        ],
        "features": [{"topic_id": "recover-original-prompt", "title": "还没找到原会话时，先搜索自己写过的提示", "why": "示例里的 music-notes 请求反复提到寻找原话；提示历史提供了另一个检索入口。", "when": "在 CLI 中需要找回以前写过的需求；这不等于恢复完整会话。", "benefit": "记不起会话位置时，不必从头重写已经表达过的要求。", "command": "Ctrl+R 搜索提示历史；Enter 使用匹配项，Esc 取消。", "availability": "reference", "version": "本地官方资料摘要；未核对本机绑定", "checked_at": end.isoformat(), "source": usage["knowledge"][0]["source"], "knowledge_refs": ["cli-interaction"], "refs": request_refs["music-notes"][:2]}],
        "latest": {"enabled": False, "status": "off", "checked_at": None, "sources": [], "note": "本次离线生成。资料日期与本次查询日期分开记录；速查表不计作新建议。"},
        "history_groups": [{"topic_id": "plan-first", "title": "计划先行", "action": "目标或边界尚不明确时，先整理计划与待决定项。", "items": [item["id"] for item in usage["history"]["items"][:2]]}],
        "confirmed_advice": [{"topic_id": "ascii-design", "title": "先画 ASCII 草图", "action": "先用 ASCII 草图对齐布局与流程，再开始实现。", "confirmed_at": "2026-09-15", "note": "合成示例：用户确认曾收到这个建议；没有伪造旧报告出处。", "projects": []}],
        "limitations": ["全部数据和分析均为合成示例，不代表真实个人习惯。", "示例未核实功能可用性，也未应用任何建议。", "记录频次不等于人工操作次数；无法辨认的分叉历史可能重复。"],
    }
    for finding, topic in zip(analysis["findings"], ["resume-current-task", "restate-constraints", "retain-live-feedback"]):
        finding["topic_id"] = topic
    new_file(folder / "usage.json", json.dumps(usage, ensure_ascii=False, indent=2) + "\n")
    new_file(folder / "analysis.json", json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")
    new_file(folder / "report.html", render(usage, analysis))
    return usage, analysis
