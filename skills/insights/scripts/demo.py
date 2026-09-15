#!/usr/bin/env python3
"""Create a clearly labelled synthetic report without reading personal history."""

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from collect import collect
from render import render
from storage import create_report_dir, new_file


def make_demo(folder=None):
    if folder is None:
        folder = create_report_dir()
    else:
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
        for j, prompt in enumerate(prompts[i % 3]):
            records.append({"timestamp": stamp, "type": "event_msg", "payload": {"type": "user_message", "message": prompt}})
            for k in range(j + 1):
                records.append({"timestamp": stamp, "type": "response_item", "payload": {"type": "function_call", "name": "functions.exec_command", "call_id": sid + "-" + str(j) + "-" + str(k), "arguments": json.dumps({"cmd": ["git status --short", "rg --files", "pnpm test"][j]})}})
        new_file(source / "sessions" / (sid + ".jsonl"), "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n")
    usage = collect(source, end - timedelta(days=89), end, ZoneInfo("Asia/Shanghai"))
    usage["demo"] = True
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
        "features": [{"title": "跨项目找回上次的会话", "why": "当任务在不同目录之间切换时，一个跨目录的会话入口可能正好减少寻找。", "command": "codex resume --all", "availability": "unverified", "version": "合成示例；实际使用时核对本机版本", "checked_at": end.isoformat(), "source": {"title": "待执行 codex resume --help", "url": None}, "refs": request_refs["music-notes"][:2]}],
        "latest": {"enabled": True, "status": "unavailable", "checked_at": None, "sources": [], "note": "合成示例没有执行网络查询。真实运行会根据开关读取官方文档，并标记实际查询状态。"},
        "limitations": ["全部数据和分析均为合成示例，不代表真实个人习惯。", "示例未核实功能可用性，也未应用任何建议。", "记录频次不等于人工操作次数；无法辨认的分叉历史可能重复。"],
    }
    new_file(folder / "usage.json", json.dumps(usage, ensure_ascii=False, indent=2) + "\n")
    new_file(folder / "analysis.json", json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")
    new_file(folder / "report.html", render(usage, analysis))
    print("Rendered synthetic example: " + str(folder / "report.html"))
    print("Report directory: " + str(folder))
    return usage, analysis


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", help="explicit new directory; default: ${TREEFOLK_HOME:-~/.treefolk}/insights/<timestamp>/")
    args = parser.parse_args()
    try:
        make_demo(args.output_dir)
    except (OSError, ValueError) as error:
        parser.exit(2, "demo: " + str(error) + "\n")
