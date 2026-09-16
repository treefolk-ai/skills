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

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from collect import collect, command_family, excerpt
from fixtures import make_report
from render import render
from storage import create_report_dir, new_file
from context import advice_id, bundled_knowledge, effective_knowledge, load_context


class InsightsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="treefolk-insights-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        isolated = patch.dict(os.environ, {"TREEFOLK_HOME": str(self.root / "treefolk")})
        isolated.start()
        self.addCleanup(isolated.stop)
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
        script = SCRIPTS / "collect.py"
        result = subprocess.run([sys.executable, "-B", str(script), "--source", str(self.root), "--until", "2026-09-15", "--timezone", "Asia/Shanghai"], cwd=project, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = Path(json.loads(result.stdout)["output"])
        self.assertEqual(output.parent.parent, base / "insights")
        self.assertTrue(output.is_file())
        self.assertEqual(list(project.iterdir()), [])

    def test_render_cli_keeps_html_with_collected_data(self):
        make_report(self.root / "render-input")
        folder = self.root / "render-input"
        (folder / "report.html").unlink()
        script = SCRIPTS / "render.py"
        result = subprocess.run([sys.executable, "-B", str(script), "--usage", str(folder / "usage.json"), "--analysis", str(folder / "analysis.json")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((folder / "report.html").is_file())
        self.assertIn(str(folder), result.stdout)

    def test_render_real_counts_and_escape_hostile_text(self):
        usage, analysis = make_report(self.root / "demo")
        self.assertEqual(len(usage["sessions"]), 15)
        self.assertEqual(sum(r["requests"] for r in usage["activity"]), 45)
        analysis["summary"] = '</script><script>window.__injected=true</script>'
        html = render(usage, analysis)
        self.assertNotIn(analysis["summary"], html)
        self.assertIn("\\u003c/script\\u003e", html)
        self.assertNotIn('"source": "sessions/', html)
        self.assertEqual(html.count("<script"), 2)
        embedded = html.split('<script id="report-data" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(json.loads(embedded)["analysis"]["summary"], analysis["summary"])

    def test_render_rejects_fabricated_refs_status_and_unsafe_links(self):
        usage, analysis = make_report(self.root / "demo")
        fabricated = copy.deepcopy(analysis)
        fabricated["suggestions"][0]["refs"] = ["nonexistent:L1"]
        with self.assertRaises(ValueError):
            render(usage, fabricated)
        bad_switch = copy.deepcopy(analysis)
        bad_switch["latest"]["enabled"] = True
        with self.assertRaises(ValueError):
            render(usage, bad_switch)
        unsafe = copy.deepcopy(usage)
        unsafe["knowledge"][0]["source"]["url"] = "javascript:alert(1)"
        with self.assertRaises(ValueError):
            render(unsafe, analysis)

    def test_cli_default_90_days_and_invalid_range_has_no_output(self):
        self.save("one.jsonl", [self.meta(), self.event()])
        script = SCRIPTS / "collect.py"
        out = self.root / "usage.json"
        base = [sys.executable, "-B", str(script), "--source", str(self.root), "--until", "2026-09-15", "--timezone", "Asia/Shanghai", "--output", str(out)]
        result = subprocess.run(base, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(out.read_text())["period"]["since"], "2026-06-18")
        invalid = self.root / "invalid.json"
        result = subprocess.run(base[:-1] + [str(invalid), "--since", "2026-10-01"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(invalid.exists())

    def token(self, incoming, outgoing, cached="missing", at="2026-09-10T00:00:00Z", initial=False, last=None):
        total = {"input_tokens": incoming, "output_tokens": outgoing, "reasoning_output_tokens": 77}
        if cached != "missing":
            total["cached_input_tokens"] = cached
        info = {"total_token_usage": total, "last_token_usage": total if initial else last}
        return {"timestamp": at, "type": "event_msg", "payload": {"type": "token_count", "info": info}}

    def test_token_used_excludes_cache_and_does_not_add_reasoning_twice(self):
        self.save("usage.jsonl", [self.meta(), self.token(1225729, 15348, 1132800, initial=True)])
        totals = self.collect()["token_usage"]
        self.assertEqual(totals["used_tokens"], 108277)
        self.assertAlmostEqual(totals["cache_hit_rate"], 1132800 / 1225729)

    def test_token_deltas_retain_pre_window_baseline_and_ignore_duplicate_snapshots(self):
        baseline = self.token(10000, 400, 8000, at="2026-08-31T00:00:00Z")
        first = self.token(15000, 550, 13000)
        self.save("old.jsonl", [self.meta(), baseline, first, first, self.token(18000, 800, 14500, at="2026-09-11T00:00:00Z")])
        usage = self.collect()
        totals = usage["token_usage"]
        self.assertEqual((totals["input_tokens"], totals["output_tokens"], totals["cached_input_tokens"], totals["used_tokens"]), (8000, 400, 6500, 1900))
        self.assertEqual(totals["coverage"]["duplicates"], 1)
        self.assertNotIn("unknown_baseline", totals["coverage"])
        self.assertEqual(usage["activity"][0]["tokens"]["used_tokens"], 150)

    def test_token_reset_and_unknown_initial_baseline_do_not_count_whole_snapshots(self):
        self.save("reset.jsonl", [self.meta(), self.token(1000, 100, 800, initial=True), self.token(100, 20, 80), self.token(300, 40, 150)])
        totals = self.collect()["token_usage"]
        self.assertEqual((totals["input_tokens"], totals["output_tokens"], totals["used_tokens"]), (1200, 120, 450))
        self.assertEqual(totals["coverage"]["counter_resets"], 1)
        self.save("unknown.jsonl", [self.meta("b", "/unknown"), self.token(900000, 1000, 800000), self.token(901000, 1100, 800900)])
        unknown = self.collect(project="/unknown")["token_usage"]
        self.assertEqual(unknown["used_tokens"], 200)
        self.assertEqual(unknown["coverage"]["unknown_baseline"], 1)

    def test_missing_cache_is_not_zero_and_coverage_follows_measurable_intervals(self):
        self.save("partial.jsonl", [self.meta(), self.token(100, 10, initial=True), self.token(200, 30, 150), self.token(400, 60, 250)])
        self.save("no-tokens.jsonl", [self.meta("b"), self.event()])
        totals = self.collect()["token_usage"]
        self.assertEqual((totals["input_tokens"], totals["output_tokens"], totals["cache_eligible_input_tokens"], totals["used_tokens"]), (400, 60, 200, 130))
        self.assertEqual(totals["coverage"]["measured"], 3)
        self.assertEqual(totals["coverage"]["cache_known"], 1)
        self.assertEqual(totals["sessions"], ["a"])
        self.assertEqual(totals["cache_hit_rate"], .5)

    def test_token_weighting_zero_denominator_project_filter_and_subagents(self):
        self.save("a.jsonl", [self.meta("a", "/project/a"), self.token(100, 10, 90, initial=True)])
        self.save("b.jsonl", [self.meta("b", "/project/b"), self.token(900, 20, 0, initial=True)])
        self.save("zero.jsonl", [self.meta("z", "/zero"), self.token(0, 0, 0, initial=True)])
        self.save("agent.jsonl", [self.meta("agent", source={"subagent": {}}), self.token(999999, 100, 0, initial=True)])
        self.assertEqual(self.collect()["token_usage"]["cache_hit_rate"], .09)
        self.assertEqual(self.collect(project="/project/b")["token_usage"]["cache_hit_rate"], 0)
        zero = self.collect(project="/zero")["token_usage"]
        self.assertIsNone(zero["cache_hit_rate"])
        self.assertEqual(zero["used_tokens"], 0)

    def test_invalid_token_counters_and_absent_usage_leave_gaps(self):
        missing = {"timestamp": "2026-09-10T00:00:00Z", "type": "event_msg", "payload": {"type": "token_count", "info": None}}
        self.save("bad.jsonl", [self.meta(), self.token(100, 10, 200, initial=True), missing, self.token(200, None), self.token(400, 40, 300)])
        totals = self.collect()["token_usage"]
        self.assertIsNone(totals["input_tokens"])
        self.assertIsNone(totals["cached_input_tokens"])
        self.assertEqual(totals["coverage"], {"snapshots": 4, "invalid_usage": 2, "missing_usage": 1, "unknown_baseline": 1})

    def test_out_of_order_token_snapshots_are_not_attributed_to_an_earlier_day(self):
        self.save("unordered.jsonl", [self.meta(), self.token(100, 10, 80, initial=True), self.token(200, 20, 160, at="2026-09-09T00:00:00Z"), self.token(300, 30, 240)])
        usage = self.collect()
        self.assertIsNone(usage["activity"][0]["tokens"]["input_tokens"])
        self.assertEqual(usage["token_usage"]["input_tokens"], 100)
        self.assertEqual(usage["token_usage"]["coverage"]["out_of_order"], 1)

    def prior(self, name, action="Use a separate checkout", day="2026-09-01", cwd="/demo/project", sid="old", demo=False, analysis_extra=None):
        folder = self.root / "reports" / name
        folder.mkdir(parents=True)
        session = {"id": sid, "project": "project"}
        if cwd is not None:
            session["cwd"] = cwd
        usage = {"schema_version": 1, "host": "codex", "status": "COLLECTED", "demo": demo, "generated_at": day + "T00:00:00Z", "sessions": [session], "evidence": [{"id": sid + ":L2", "session": sid}]}
        analysis = {"summary": "Prior report", "suggestions": [{"title": "A useful suggestion", "action": action, "refs": [sid + ":L2"]}], **(analysis_extra or {})}
        new_file(folder / "usage.json", json.dumps(usage))
        new_file(folder / "analysis.json", json.dumps(analysis))
        new_file(folder / "report.html", "<!doctype html><title>Prior synthetic report</title>")
        return folder

    def context(self, **kwargs):
        return load_context(self.root / "reports", self.root / "reports" / "current", **kwargs)

    def test_history_dedup_keeps_latest_source_and_ignores_copied_history(self):
        self.prior("one", day="2026-08-01")
        self.prior("two", action="  USE a separate   checkout ", day="2026-09-02", analysis_extra={"history_groups": [{"title": "DO NOT REIMPORT COPIED HISTORY"}]})
        context = self.context()
        items = context["history"]["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual((items[0]["last_seen"], items[0]["report_id"]), ("2026-09-02", "two"))
        self.assertNotIn("DO NOT REIMPORT", json.dumps(context))

    def test_history_skips_demos_incomplete_invalid_and_linked_reports(self):
        self.prior("valid")
        self.prior("demo", demo=True)
        (self.prior("incomplete") / "analysis.json").unlink()
        (self.prior("invalid") / "usage.json").write_text("{broken")
        linked = self.prior("linked") / "report.html"
        linked.unlink()
        linked.symlink_to(self.root / "reports" / "valid" / "report.html")
        result = self.context()["history"]
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["coverage"]["demo_reports"], 1)
        self.assertEqual(result["coverage"]["incomplete_reports"], 1)
        self.assertEqual(result["coverage"]["invalid_reports"], 2)

    def test_history_project_attribution_uses_paths_or_proven_session_ids(self):
        self.prior("unknown", action="Unknown project advice", cwd=None)
        self.prior("wrong", action="Wrong project advice", cwd="/elsewhere/project", sid="elsewhere")
        self.prior("selected", action="Selected project advice", cwd="/demo/project/sub", sid="selected")
        result = self.context(project="/demo/project")
        self.assertEqual([i["action"] for i in result["history"]["items"]], ["Selected project advice"])
        recovered = self.context(project="/demo/project", current_sessions=[{"id": "old", "cwd": "/demo/project"}])
        self.assertEqual(len(recovered["history"]["items"]), 2)
        self.assertEqual(self.context(max_reports=1)["history"]["coverage"]["report_limit_excluded"], 2)

    def test_offline_context_and_arbitrary_new_document_snapshots(self):
        doc = {"id": "a-new-document-not-in-the-package", "source": {"title": "An official page", "url": "https://learn.chatgpt.com/docs/prompting"}, "source_date": "2026-09-14", "text": "Older saved facts"}
        def queried(item):
            return {"latest": {"enabled": True, "status": "checked", "checked_at": item["source_date"], "sources": [item["source"]]}, "knowledge_updates": [item]}
        self.prior("z-older", analysis_extra=queried(doc))
        fresh = dict(doc, source_date="2026-09-15", text="Newly saved facts")
        self.prior("a-newer", analysis_extra=queried(fresh))
        with patch("socket.socket", side_effect=AssertionError("offline flow tried to access network")):
            docs = self.context()["knowledge"]
        reused = next(d for d in docs if d["id"] == doc["id"])
        self.assertEqual(reused["text"], "Newly saved facts")
        self.assertEqual(reused["origin"], "prior_query")
        for latest in [{"enabled": False, "status": "off"}, {"enabled": True, "status": "unavailable"}]:
            with self.assertRaises(ValueError):
                effective_knowledge(bundled_knowledge(), {"latest": latest, "knowledge_updates": [fresh]})
        partial = queried(fresh)
        partial["latest"]["status"] = "partial"
        self.assertIn(fresh["id"], {d["id"] for d in effective_knowledge([], partial)})

    def test_repeated_advice_requires_specific_increment_and_topics_are_open(self):
        usage, analysis = make_report(self.root / "novelty")
        feature = analysis["suggestions"][0]
        feature["topic_id"] = "a-useful-new-approach-outside-the-reference-index"
        render(usage, analysis)  # No allowlist of recommendation topics.
        feature["topic_id"] = "plan-first"
        with self.assertRaisesRegex(ValueError, "new_detail"):
            render(usage, analysis)
        feature["new_detail"] = "A new trigger and operation demonstrated by this run's evidence."
        render(usage, analysis)
        feature.pop("new_detail")
        feature["topic_id"] = "renaming-does-not-hide-the-same-action"
        feature["action"] = usage["history"]["items"][0]["action"]
        with self.assertRaisesRegex(ValueError, "new_detail"):
            render(usage, analysis)

    def test_three_suggestions_and_optional_trial_require_a_real_instruction(self):
        usage, analysis = make_report(self.root / "simple")
        self.assertEqual(sum("try" in i for i in analysis["suggestions"]), 1)
        for field in ("where", "text", "expect"):
            broken = copy.deepcopy(analysis)
            broken["suggestions"][1]["try"].pop(field)
            with self.assertRaisesRegex(ValueError, field):
                render(usage, broken)
        too_many = copy.deepcopy(analysis)
        too_many["suggestions"].append(dict(too_many["suggestions"][0], action="A fourth idea"))
        with self.assertRaisesRegex(ValueError, "at most three"):
            render(usage, too_many)
        duplicate = copy.deepcopy(analysis)
        duplicate["suggestions"][1] = duplicate["suggestions"][0]
        with self.assertRaisesRegex(ValueError, "duplicate suggestion"):
            render(usage, duplicate)
        self.assertIn('"suggestions": []', render(usage, dict(analysis, suggestions=[])))

    def test_collect_leaves_retired_known_file_untouched(self):
        self.save("one.jsonl", [self.meta(), self.event()])
        base = self.root / "treefolk" / "insights"
        base.mkdir(parents=True)
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "collect.py"), "--source", str(self.root), "--until", "2026-09-15"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((base / "known.md").exists())
        new_file(base / "known.md", "Private handwritten notes; not a valid old feedback file")
        # A retired file must neither change nor make a valid collection partial.
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS / "collect.py"), "--source", str(self.root), "--until", "2026-09-15"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        info = json.loads(result.stdout)
        self.assertEqual(info["status"], "COLLECTED")
        self.assertNotIn("feedback", json.loads(Path(info["output"]).read_text()))
        self.assertEqual((base / "known.md").read_text(), "Private handwritten notes; not a valid old feedback file")

    def test_legacy_history_imports_only_original_displayed_advice(self):
        folder = self.prior("legacy")
        usage = json.loads((folder / "usage.json").read_text())
        usage.update(suggestion_selection="random-v1", feedback={"entries": [{"id": advice_id("Already hidden"), "known": True}]})
        analysis = {"findings": [{"title": "Hidden finding", "action": "Already hidden", "refs": ["old:L2"]}], "features": [{"title": command, "command": command, "refs": ["old:L2"]} for command in ["Already hidden", "Visible one", "Visible two"]], "history_groups": [{"action": "Copied history"}], "confirmed_advice": [{"action": "Copied confirmation"}]}
        (folder / "usage.json").write_text(json.dumps(usage))
        (folder / "analysis.json").write_text(json.dumps(analysis))
        result = self.context()
        self.assertEqual({i["action"] for i in result["history"]["items"]}, {"Visible one", "Visible two"})
        self.assertNotIn("feedback", result)

    def test_private_context_stays_out_of_html_and_trial_text_is_escaped(self):
        usage, analysis = make_report(self.root / "private")
        hostile = '</script><img src=x onerror=alert(1)>'
        usage["history"]["items"][0]["title"] = "PRIVATE PRIOR ADVICE"
        usage["knowledge"][0]["text"] = "FULL LOCAL DOCUMENT TEXT"
        usage["feedback"] = {"path": "/private/known.md", "entries": []}
        analysis["suggestions"][1]["try"]["text"] = hostile
        html = render(usage, analysis)
        for private in (hostile, "PRIVATE PRIOR ADVICE", "FULL LOCAL DOCUMENT TEXT", "/private/known.md", "/demo/music-notes"):
            self.assertNotIn(private, html)
        embedded = json.loads(html.split('<script id="report-data" type="application/json">', 1)[1].split('</script>', 1)[0])
        self.assertEqual(embedded["analysis"]["suggestions"][1]["try"]["text"], hostile)
        self.assertNotIn("history", embedded)
        self.assertNotIn("feedback", embedded)
        # Earlier usage exports may lack token snapshots or history.
        for key in ("history", "token_usage"):
            usage.pop(key, None)
        for row in usage["activity"]:
            row.pop("tokens", None)
        render(usage, analysis)


if __name__ == "__main__":
    unittest.main()
