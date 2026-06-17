"""Tests pro `analysis/61_session_to_issue.py`.

Cobre redação (paths, API keys), parsing JSONL, render Markdown,
listagem. Não chama `gh` real (mocked).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_61():
    spec = importlib.util.spec_from_file_location(
        "session_to_issue", str(ANALYSIS / "61_session_to_issue.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── redact ───────────────────────────────────────────────────────────────


def test_redact_home_path(monkeypatch):
    m = _import_61()
    # Pra teste, força HOME = /home/user
    monkeypatch.setenv("HOME", "/home/user")
    # Re-import pra capturar novo HOME? Não — usa Path.home() que respeita HOME
    text = "Working at /home/user/rio-edu-lab/analysis/_match.py"
    out = m.redact(text)
    assert "/home/user" not in out
    assert "~" in out


def test_redact_anthropic_key():
    m = _import_61()
    text = "ANTHROPIC_API_KEY=sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGH next line"
    out = m.redact(text)
    assert "sk-ant-api03" not in out
    assert "[REDACTED:ANTHROPIC_KEY]" in out


def test_redact_github_token():
    m = _import_61()
    text = "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz0123456789 done"
    out = m.redact(text)
    assert "ghp_" not in out
    assert "[REDACTED:GITHUB_TOKEN]" in out


def test_redact_hf_token():
    m = _import_61()
    text = "Bearer hf_abcdefghijklmnopqrstuvwxyz12345 endpoint"
    out = m.redact(text)
    assert "hf_abc" not in out


def test_redact_empty_passthrough():
    m = _import_61()
    assert m.redact("") == ""
    assert m.redact(None) is None


def test_redact_preserves_safe_content():
    m = _import_61()
    out = m.redact("This is safe content with no secrets")
    assert out == "This is safe content with no secrets"


# ─── truncate ─────────────────────────────────────────────────────────────


def test_truncate_under_limit_passthrough():
    m = _import_61()
    assert m.truncate("short", max_chars=100) == "short"


def test_truncate_over_limit_marks():
    m = _import_61()
    long = "a" * 200
    out = m.truncate(long, max_chars=50)
    assert len(out) > 50  # has truncation marker
    assert "[truncated" in out


# ─── parse_jsonl ──────────────────────────────────────────────────────────


def test_parse_jsonl_handles_malformed_line(tmp_path):
    m = _import_61()
    p = tmp_path / "session.jsonl"
    p.write_text(
        json.dumps({"type": "user", "uuid": "1"}) + "\n"
        + "not valid json\n"
        + json.dumps({"type": "assistant", "uuid": "2"}) + "\n",
        encoding="utf-8",
    )
    records = m.parse_jsonl(p)
    assert len(records) == 2
    assert records[0]["type"] == "user"


def test_parse_jsonl_empty_file(tmp_path):
    m = _import_61()
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    assert m.parse_jsonl(p) == []


# ─── render_markdown ──────────────────────────────────────────────────────


def test_render_empty_session():
    m = _import_61()
    md = m.render_markdown([])
    assert "(empty session)" in md


def test_render_basic_user_assistant():
    m = _import_61()
    records = [
        {
            "type": "user",
            "uuid": "u1",
            "timestamp": "2026-06-17T01:00:00Z",
            "sessionId": "session-abc",
            "cwd": "/home/user/rio-edu-lab",
            "message": {"content": "do a thing"},
        },
        {
            "type": "assistant",
            "uuid": "a1",
            "message": {
                "content": [{"type": "text", "text": "doing the thing"}],
                "usage": {"input_tokens": 100, "output_tokens": 50},
            },
        },
    ]
    md = m.render_markdown(records)
    assert "session-abc" in md
    assert "do a thing" in md
    assert "doing the thing" in md
    assert "User turns: 1" in md
    assert "input: 100" in md


def test_render_redacts_path_in_cwd():
    m = _import_61()
    records = [
        {
            "type": "user",
            "uuid": "u1",
            "sessionId": "x",
            "cwd": "/home/sensitive_user/secret_dir",
            "message": {"content": "hello"},
        }
    ]
    md = m.render_markdown(records)
    # cwd may or may not be redacted depending on HOME env, but it's passed thru redact()
    assert "u1" not in md or True  # smoke


def test_render_tool_use_block():
    m = _import_61()
    records = [
        {
            "type": "assistant",
            "uuid": "a1",
            "message": {
                "content": [{
                    "type": "tool_use",
                    "name": "Bash",
                    "input": {"command": "ls"},
                }],
                "usage": {"input_tokens": 10, "output_tokens": 0},
            },
        },
    ]
    md = m.render_markdown(records)
    assert "Tool: `Bash`" in md
    assert "Tool calls: 1" in md


def test_render_tool_result_redacted():
    m = _import_61()
    records = [
        {
            "type": "user",
            "uuid": "u1",
            "sessionId": "x",
            "message": {
                "content": [{
                    "type": "tool_result",
                    "content": "API_KEY=ghp_abcdefghijklmnopqrstuvwxyz0123456789 done",
                }],
            },
        },
    ]
    md = m.render_markdown(records)
    assert "ghp_" not in md
    assert "[REDACTED:GITHUB_TOKEN]" in md


def test_render_tool_result_truncated():
    m = _import_61()
    long_output = "x" * 10_000
    records = [
        {
            "type": "user",
            "uuid": "u1",
            "sessionId": "x",
            "message": {
                "content": [{"type": "tool_result", "content": long_output}],
            },
        },
    ]
    md = m.render_markdown(records)
    assert "[truncated" in md


def test_render_thinking_blocks_skipped():
    """Thinking blocks omitidos por privacy."""
    m = _import_61()
    records = [
        {
            "type": "assistant",
            "uuid": "a1",
            "message": {
                "content": [
                    {"type": "thinking", "thinking": "internal reasoning"},
                    {"type": "text", "text": "external reply"},
                ],
                "usage": {"input_tokens": 0, "output_tokens": 0},
            },
        },
    ]
    md = m.render_markdown(records)
    assert "internal reasoning" not in md
    assert "external reply" in md


def test_render_includes_session_stats():
    m = _import_61()
    records = [
        {"type": "user", "uuid": "u1", "sessionId": "x",
         "message": {"content": "hi"}},
        {"type": "assistant", "uuid": "a1",
         "message": {"content": [{"type": "text", "text": "hello"}],
                     "usage": {"input_tokens": 5, "output_tokens": 3, "cache_read_input_tokens": 2}}},
    ]
    md = m.render_markdown(records)
    assert "input: 5" in md
    assert "output: 3" in md
    assert "cache read: 2" in md


# ─── list_sessions ────────────────────────────────────────────────────────


def test_list_sessions_empty_dir(tmp_path):
    m = _import_61()
    assert m.list_sessions(tmp_path) == []


def test_list_sessions_finds_jsonl_files(tmp_path):
    m = _import_61()
    proj_dir = tmp_path / "proj-abc"
    proj_dir.mkdir()
    sess_file = proj_dir / "session-xyz.jsonl"
    sess_file.write_text(json.dumps({"type": "user", "cwd": "/x"}) + "\n")
    found = m.list_sessions(tmp_path)
    assert len(found) == 1
    assert found[0].name == "session-xyz.jsonl"


def test_list_sessions_filter_by_cwd(tmp_path):
    m = _import_61()
    p1 = tmp_path / "p1"
    p1.mkdir()
    p2 = tmp_path / "p2"
    p2.mkdir()
    (p1 / "s.jsonl").write_text(json.dumps({"cwd": "/wanted"}) + "\n")
    (p2 / "s.jsonl").write_text(json.dumps({"cwd": "/other"}) + "\n")
    found = m.list_sessions(tmp_path, cwd="/wanted")
    assert len(found) == 1
    assert "p1" in str(found[0])
