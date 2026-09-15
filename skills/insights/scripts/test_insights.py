#!/usr/bin/env python3
"""Behavioral checks using synthetic sources only; no network or home-directory reads."""

import copy
from datetime import date
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from collect import collect, command_family, excerpt
from demo import make_demo
from render import render
from storage import create_report_dir, new_file


class InsightsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="treefolk-insights-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "sessions").mkdir()
        self.start = date(2026, 9, 1)
        self.end = date(2026, 9, 15)
        self.tz = ZoneInfo("Asia/Shanghai")

    def save(self, name, records):
        path = self.root / "sessions" / name
        new_file(path, "\n".join(json.dumps(record) for record in records) + "\n")
        return path

    def meta(self, sid="a", cwd="/demo/project", source="cli"):
        return {"timestamp": "2026-01-01T00:00:00Z", "type": "session_meta", "payload": {"id": sid, "cwd": cwd, "source": source}}

    def event(self, text="Continue the task", at="2026-09-10T00:00:00Z"):
        return {"timestamp": at, "type": "event_msg", "payload": {"type": "user_message", "message": text}}

    def collect(self, **kwargs):
        return collect(self.root, self.start, self.end, self.tz, **kwargs)

    def test_calendar_boundaries_and_resumed_old_session(self):
        self.save("old.jsonl", [self.meta(), self.event(at="2026-08-31T15:59:59Z"), self.event(at="2026-08-31T16:00:00Z"), self.event(at="2026-09-15T15:59:59Z"), self.event(at="2026-09-15T16:00:00Z")])
        result = self.collect()
        self.assertEqual([row["date"] for row in result["activity"]], ["2026-09-01", "2026-09-15"])
        self.assertEqual(sum(r["requests"] for r in result["activity"]), 2)

    def test_no_double_counting_messages_calls_or_session_files(self):
        call = {"timestamp": "2026-09-10T00:00:00Z", "type": "response_item", "payload": {"type": "function_call", "call_id": "call-1", "name": "functions.exec_command", "arguments": '{"cmd":"git status --short"}'}}
        echoed = {"timestamp": "2026-09-10T00:00:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "$build Add a filter"}]}}
        data = [self.meta(), self.event("$build Add a filter"), echoed, call, call]
        self.save("original.jsonl", data)
        self.save("copy.jsonl", data)
        result = self.collect()
        self.assertEqual(len(result["sessions"]), 1)
        self.assertEqual(result["activity"][0]["requests"], 1)
        self.assertEqual(result["activity"][0]["tools"], 1)
        self.assertEqual(result["activity"][0]["skills"], {"build": 1})
        self.assertEqual(result["coverage"]["duplicate_session_files"], 1)

    def test_scope_subagents_symlinks_and_same_basename(self):
        self.save("one.jsonl", [self.meta("a", "/demo/project"), self.event()])
        self.save("two.jsonl", [self.meta("b", "/elsewhere/project"), self.event()])
        self.save("neighbor.jsonl", [self.meta("c", "/demo/project-two"), self.event()])
        self.save("agent.jsonl", [self.meta("agent", source={"subagent": {"spawn": {}}}), self.event()])
        outside = self.root / "private.jsonl"
        new_file(outside, json.dumps(self.meta("private")) + "\n" + json.dumps(self.event("should never be read")) + "\n")
        (self.root / "sessions" / "linked.jsonl").symlink_to(outside)
        result = self.collect()
        self.assertEqual(len(result["sessions"]), 3)
        self.assertEqual(len({s["project"] for s in result["sessions"]}), 3)
        self.assertNotIn("should never be read", json.dumps(result))
        selected = self.collect(project="/demo/project")
        self.assertEqual([s["id"] for s in selected["sessions"]], ["a"])

    def test_unknown_broken_and_limited_sources_are_visible(self):
        self.save("unknown.jsonl", [{"some": "other log format"}])
        path = self.save("valid.jsonl", [self.meta(), self.event()])
        with path.open("ab") as file:
            file.write(b"{broken\n")
        result = self.collect()
        self.assertEqual(result["coverage"]["unsupported_files"], 1)
        self.assertEqual(result["coverage"]["malformed_lines"], 1)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(self.collect(max_files=1)["coverage"]["file_limit_excluded"], 1)
        with patch("collect.MAX_FILE_BYTES", 60):
            self.assertGreater(self.collect()["coverage"]["truncated_files"], 0)

    def test_fallback_ignores_injected_user_context(self):
        def message(text):
            return {"timestamp": "2026-09-10T00:00:00Z", "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}}
        self.save("fallback.jsonl", [self.meta(), message("# AGENTS.md instructions for project"), message("A real request")])
        result = self.collect()
        self.assertEqual(result["activity"][0]["requests"], 1)
        self.assertEqual(result["coverage"]["fallback_message_files"], 1)

    def test_minimization_and_command_data_never_executes(self):
        self.assertNotIn("secret-value", excerpt("api_key=secret-value"))
        self.assertNotIn("person@example.com", excerpt("contact person@example.com"))
        self.assertNotIn("/Users/test/private", excerpt("open /Users/test/private/file"))
        marker = self.root / "executed"
        payload = {"name": "exec_command", "arguments": json.dumps({"cmd": "echo $(touch " + str(marker) + ")"})}
        self.assertEqual(command_family(payload), "复合 shell 命令")
        self.assertFalse(marker.exists())

    def test_malformed_tool_fields_and_duplicate_failures_preserve_partial_data(self):
        bad_call = {"timestamp": "2026-09-10T00:00:00Z", "type": "response_item", "payload": {"type": "function_call", "call_id": {}, "name": ["not", "a", "name"]}}
        result = {"timestamp": "2026-09-10T00:00:00Z", "type": "response_item", "payload": {"type": "function_call_output", "call_id": "failed-1", "output": {"exit_code": 1}}}
        self.save("partial.jsonl", [self.meta(), self.event(), bad_call, result, result])
        usage = self.collect()
        self.assertEqual(usage["activity"][0]["errors"], 1)
        self.assertEqual(usage["activity"][0]["requests"], 1)
        self.assertEqual(usage["coverage"]["unknown_tool_names"], 1)
        self.assertEqual(usage["coverage"]["unsupported_call_ids"], 1)

    def test_archives_empty_window_and_missing_source_are_distinct(self):
        path = self.save("archived.jsonl", [self.meta(), self.event()])
        archive = self.root / "archived_sessions"
        archive.mkdir()
        path.rename(archive / path.name)
        self.assertEqual(len(self.collect()["sessions"]), 1)
        empty = collect(self.root, date(2025, 1, 1), date(2025, 1, 2), self.tz)
        self.assertEqual(empty["sessions"], [])
        self.assertEqual(empty["status"], "NO-DATA")
        self.assertEqual(empty["coverage"]["outside_window_or_empty"], 1)
        with self.assertRaises(ValueError):
            collect(archive, self.start, self.end, self.tz)
        self.save("unknown.jsonl", [{"another": "format"}])
        broken = collect(self.root, date(2025, 1, 1), date(2025, 1, 2), self.tz)
        self.assertEqual(broken["status"], "BLOCKED")

    def test_output_refuses_overwrite_and_symlink(self):
        out = self.root / "report.html"
        new_file(out, "keep this")
        with self.assertRaises(FileExistsError):
            new_file(out, "replacement")
        self.assertEqual(out.read_text(), "keep this")
        self.assertEqual(out.stat().st_mode & 0o777, 0o600)
        link = self.root / "link.html"
        link.symlink_to(out)
        with self.assertRaises(FileExistsError):
            new_file(link, "replacement")

    def test_default_report_storage_is_private_unique_and_preserves_other_data(self):
        base = self.root / "treefolk"
        base.mkdir()
        new_file(base / "user-note.txt", "keep this")
        with patch.dict(os.environ, {"TREEFOLK_HOME": str(base)}):
            first = create_report_dir()
            second = create_report_dir()
        self.assertEqual(first.parent, base / "insights")
        self.assertNotEqual(first, second)
        self.assertEqual(first.stat().st_mode & 0o777, 0o700)
        self.assertEqual((base / "user-note.txt").read_text(), "keep this")

    def test_report_storage_conflict_does_not_redirect_or_fallback(self):
        base = self.root / "treefolk"
        base.mkdir()
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (base / "insights").symlink_to(elsewhere, target_is_directory=True)
        with patch.dict(os.environ, {"TREEFOLK_HOME": str(base)}):
            with self.assertRaisesRegex(ValueError, "symlink: .*insights$"):
                create_report_dir()
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_report_storage_accepts_parent_alias_and_returns_physical_path(self):
        alias = self.root / "parent-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with patch.dict(os.environ, {"TREEFOLK_HOME": str(alias / "treefolk")}):
            folder = create_report_dir()
        self.assertEqual(folder.parent, self.root / "treefolk" / "insights")
        self.assertEqual(folder, folder.resolve())

    def test_collect_cli_default_storage_ignores_working_directory(self):
        self.save("one.jsonl", [self.meta(), self.event()])
        project = self.root / "working-project"
        project.mkdir()
        base = self.root / "user-store"
        env = dict(os.environ, TREEFOLK_HOME=str(base))
        script = Path(__file__).with_name("collect.py").resolve()
        result = subprocess.run([sys.executable, "-B", str(script), "--source", str(self.root), "--until", "2026-09-15", "--timezone", "Asia/Shanghai"], cwd=project, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = Path(json.loads(result.stdout)["output"])
        self.assertEqual(output.parent.parent, base / "insights")
        self.assertTrue(output.is_file())
        self.assertEqual(list(project.iterdir()), [])

    def test_render_cli_keeps_html_with_collected_data(self):
        make_demo(self.root / "render-input")
        folder = self.root / "render-input"
        (folder / "report.html").unlink()
        script = Path(__file__).with_name("render.py").resolve()
        result = subprocess.run([sys.executable, "-B", str(script), "--usage", str(folder / "usage.json"), "--analysis", str(folder / "analysis.json")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((folder / "report.html").is_file())
        self.assertIn(str(folder), result.stdout)

    def test_render_real_counts_and_escape_hostile_text(self):
        usage, analysis = make_demo(self.root / "demo")
        self.assertEqual(len(usage["sessions"]), 15)
        self.assertEqual(sum(r["requests"] for r in usage["activity"]), 45)
        analysis["summary"] = '</script><script>window.__injected=true</script>'
        html = render(usage, analysis)
        self.assertNotIn(analysis["summary"], html)
        self.assertIn("\\u003c/script\\u003e", html)
        self.assertNotIn('"source": "sessions/', html)
        self.assertEqual(html.count("<script"), 2)

    def test_render_rejects_fabricated_refs_status_and_unsafe_links(self):
        usage, analysis = make_demo(self.root / "demo")
        fabricated = copy.deepcopy(analysis)
        fabricated["findings"][0]["refs"] = ["nonexistent:L1"]
        with self.assertRaises(ValueError):
            render(usage, fabricated)
        bad_switch = copy.deepcopy(analysis)
        bad_switch["latest"]["enabled"] = False
        with self.assertRaises(ValueError):
            render(usage, bad_switch)
        unsafe = copy.deepcopy(analysis)
        unsafe["features"][0]["source"]["url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            render(usage, unsafe)

    def test_cli_default_90_days_and_invalid_range_has_no_output(self):
        self.save("one.jsonl", [self.meta(), self.event()])
        script = Path(__file__).with_name("collect.py")
        out = self.root / "usage.json"
        base = [sys.executable, "-B", str(script), "--source", str(self.root), "--until", "2026-09-15", "--timezone", "Asia/Shanghai", "--output", str(out)]
        result = subprocess.run(base, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(out.read_text())["period"]["since"], "2026-06-18")
        invalid = self.root / "invalid.json"
        result = subprocess.run(base[:-1] + [str(invalid), "--since", "2026-10-01"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(invalid.exists())


if __name__ == "__main__":
    unittest.main()
