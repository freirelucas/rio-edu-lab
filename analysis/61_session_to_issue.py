"""Claude Code session JSONL → GitHub issue Markdown.

Sprint v0.16 — implementa o canal "chat → audit trail" pedido pela missão
do lab (transparência ativa, auditabilidade um-clique). Parsea o JSONL
escrito pelo Claude Code em ~/.claude/projects/<proj>/<session-id>.jsonl
e renderiza Markdown legível, com redação pra segurança.

**Não substitui** Langfuse / LangSmith (observability rica) — é o caminho
mínimo soberano: zero dep, zero secret, output committable.

Schema JSONL (verificado em https://databunny.medium.com/inside-claude-code-...):
  Common envelope: type, uuid, parentUuid, timestamp, sessionId, cwd, message
  type ∈ {user, assistant, system, summary, result, file-history-snapshot}
  assistant.message.content[]: {type: text|tool_use|thinking, ...}
  user.message.content[]: {type: text|tool_result, ...}
  assistant.message.usage: {input_tokens, output_tokens, cache_read_*, ...}

Redação obrigatória (privacy + sec):
  - Absolute paths /home/user/... → ~/
  - API keys/tokens (sk-, ghp_, etc.) → [REDACTED]
  - Tool results > MAX_TOOL_RESULT_CHARS truncated (default 5KB)
  - Email mantido (já público em CITATION.cff)

Uso:
  # Listar sessões da working dir atual
  python3 analysis/61_session_to_issue.py --list

  # Renderizar 1 sessão pra Markdown (stdout)
  python3 analysis/61_session_to_issue.py --session <session-id>

  # Salvar arquivo
  python3 analysis/61_session_to_issue.py --session <session-id> \
    --out /tmp/session.md

  # Criar GitHub issue (precisa `gh` autenticado)
  python3 analysis/61_session_to_issue.py --session <session-id> \
    --create-issue --repo freirelucas/rio-edu-lab

  # Pegar transcript_path automaticamente (modo SessionEnd hook)
  python3 analysis/61_session_to_issue.py --transcript-path "$TRANSCRIPT_PATH"

Pra SessionEnd hook em `.claude/settings.json`:
  {"hooks": {"SessionEnd": "python3 analysis/61_session_to_issue.py
   --transcript-path \"$TRANSCRIPT_PATH\" --out audit/$(date +%Y%m%d_%H%M%S).md"}}
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SESSIONS_DIR = Path.home() / ".claude" / "projects"
MAX_TOOL_RESULT_CHARS = 5_000

# Padrões de redação (não exaustivos — last line of defense, gitleaks/trufflehog
# também rodam pre-commit/CI conforme v0.17)
REDACT_PATTERNS = [
    # API keys + tokens
    (re.compile(r"sk-ant-api\d+-[A-Za-z0-9_-]{40,}"), "[REDACTED:ANTHROPIC_KEY]"),
    (re.compile(r"sk-proj-[A-Za-z0-9_-]{40,}"), "[REDACTED:OPENAI_KEY]"),
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "[REDACTED:GITHUB_TOKEN]"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{50,}"), "[REDACTED:GITHUB_PAT]"),
    (re.compile(r"hf_[A-Za-z0-9]{30,}"), "[REDACTED:HF_TOKEN]"),
    (re.compile(r"AKIA[A-Z0-9]{16}"), "[REDACTED:AWS_KEY]"),
    # Bearer tokens generic (cuidado: pode trazer fp; só strings longas)
    (re.compile(r"Bearer\s+[A-Za-z0-9._-]{40,}"), "Bearer [REDACTED]"),
]


def list_sessions(sessions_dir: Path, cwd: str | None = None) -> list[Path]:
    """List session JSONLs, opcionalmente filtrando por working dir."""
    if not sessions_dir.exists():
        return []
    all_jsonl = sorted(sessions_dir.glob("*/*.jsonl"))
    if cwd is None:
        return all_jsonl
    # Filter by inspecting first line's cwd field
    out = []
    for p in all_jsonl:
        try:
            first_line = p.read_text(encoding="utf-8").split("\n", 1)[0]
            data = json.loads(first_line)
            if data.get("cwd") == cwd:
                out.append(p)
        except Exception:
            continue
    return out


def redact(text: str) -> str:
    """Aplica padrões de redação. Returns transformed text."""
    if not text:
        return text
    # Absolute paths: /home/user/... → ~/...
    home = str(Path.home())
    if home in text:
        text = text.replace(home, "~")
    # Other absolute path patterns (defensive)
    text = re.sub(r"/Users/[^/\s]+/", "~/", text)
    # API keys/tokens
    for pattern, replacement in REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def truncate(text: str, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n…[truncated {len(text) - max_chars} chars]"


def parse_jsonl(path: Path) -> list[dict]:
    """Parse session JSONL into list of records. Skips malformed lines."""
    records = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"  [warn] {path.name}:L{line_no} malformed JSON", file=sys.stderr)
    return records


def _content_to_md(block: dict) -> str:
    """Convert one content block (text/tool_use/tool_result/thinking) to Markdown."""
    btype = block.get("type")
    if btype == "text":
        return redact(block.get("text") or "")
    if btype == "tool_use":
        name = block.get("name") or "?"
        tool_input = block.get("input") or {}
        # Render input as code block; redact + truncate
        input_str = json.dumps(tool_input, ensure_ascii=False, indent=2)
        input_str = truncate(redact(input_str), max_chars=2000)
        return f"\n**🔧 Tool: `{name}`**\n\n```json\n{input_str}\n```\n"
    if btype == "tool_result":
        content = block.get("content")
        if isinstance(content, list):
            # multimodal — extract text only
            parts = [c.get("text", "") for c in content if c.get("type") == "text"]
            content_str = "\n".join(parts)
        else:
            content_str = str(content) if content is not None else ""
        content_str = truncate(redact(content_str))
        is_error = bool(block.get("is_error"))
        prefix = "**❌ Tool error:**" if is_error else "**📄 Tool result:**"
        return f"\n{prefix}\n\n```\n{content_str}\n```\n"
    if btype == "thinking":
        # Pulamos thinking blocks por default (privacy: pode revelar prompt
        # raciocínio interno do agente, não acrescenta valor pra audit)
        return ""
    return ""


def render_markdown(records: list[dict], title_prefix: str = "Claude Code Session") -> str:
    """Render parsed JSONL records to Markdown audit trail."""
    # Header
    if not records:
        return f"# {title_prefix}\n\n_(empty session)_\n"

    first = records[0]
    cwd = first.get("cwd", "?")
    session_id = first.get("sessionId", "?")
    first_ts = first.get("timestamp") or "?"

    lines = []
    lines.append(f"# {title_prefix}")
    lines.append("")
    lines.append(f"- **Session ID**: `{session_id}`")
    lines.append(f"- **Working dir**: `{redact(cwd)}`")
    lines.append(f"- **Started**: {first_ts}")
    lines.append(f"- **Records**: {len(records)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Total usage
    total_input = 0
    total_output = 0
    total_cache_read = 0
    n_tool_calls = 0
    n_user_turns = 0

    for rec in records:
        rtype = rec.get("type")
        msg = rec.get("message") or {}

        if rtype == "user":
            content = msg.get("content")
            n_user_turns += 1
            if isinstance(content, str):
                text = redact(content)
                if text.strip():
                    lines.append(f"## 👤 User turn {n_user_turns}")
                    lines.append("")
                    lines.append(text)
                    lines.append("")
            elif isinstance(content, list):
                # Mix de text + tool_result
                parts = [_content_to_md(b) for b in content]
                rendered = "\n".join(p for p in parts if p)
                if rendered.strip():
                    lines.append(f"## 👤 User turn {n_user_turns}")
                    lines.append("")
                    lines.append(rendered)
                    lines.append("")

        elif rtype == "assistant":
            content = msg.get("content") or []
            usage = msg.get("usage") or {}
            total_input += usage.get("input_tokens", 0) or 0
            total_output += usage.get("output_tokens", 0) or 0
            total_cache_read += usage.get("cache_read_input_tokens", 0) or 0
            for b in (content if isinstance(content, list) else []):
                if b.get("type") == "tool_use":
                    n_tool_calls += 1

            if isinstance(content, list) and content:
                parts = [_content_to_md(b) for b in content]
                rendered = "\n".join(p for p in parts if p)
                if rendered.strip():
                    lines.append("### 🤖 Assistant")
                    lines.append("")
                    lines.append(rendered)
                    lines.append("")

        elif rtype == "summary":
            summ = msg.get("summary") or msg.get("content") or ""
            if summ:
                lines.append("### 📋 Session summary")
                lines.append("")
                lines.append(redact(str(summ)))
                lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Session stats")
    lines.append("")
    lines.append(f"- User turns: {n_user_turns}")
    lines.append(f"- Tool calls: {n_tool_calls}")
    lines.append(f"- Tokens — input: {total_input:,} · output: {total_output:,} · cache read: {total_cache_read:,}")
    lines.append("")
    lines.append("_Audit trail gerado por `analysis/61_session_to_issue.py`. Redação aplicada: paths absolutos, API keys, tool results > 5KB._")

    return "\n".join(lines)


def create_github_issue(title: str, body: str, repo: str | None = None) -> int:
    """Cria issue via `gh issue create`. Requires gh autenticado.

    Returns exit code do subprocess.
    """
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    if repo:
        cmd.extend(["--repo", repo])
    try:
        result = subprocess.run(cmd, check=False, timeout=60)
        return result.returncode
    except FileNotFoundError:
        print("  [error] `gh` not found in PATH. Install: https://cli.github.com/", file=sys.stderr)
        return 127
    except subprocess.TimeoutExpired:
        print("  [error] gh issue create timeout", file=sys.stderr)
        return 124


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions-dir", type=Path, default=DEFAULT_SESSIONS_DIR,
                    help="root pra ~/.claude/projects/ (default)")
    ap.add_argument("--cwd-filter", type=str, default=None,
                    help="filter list by working dir (e.g. /home/user/rio-edu-lab)")
    ap.add_argument("--list", action="store_true",
                    help="apenas listar sessões")
    ap.add_argument("--session", type=str, default=None,
                    help="session id (filename sem .jsonl)")
    ap.add_argument("--transcript-path", type=Path, default=None,
                    help="path direto pro JSONL (modo SessionEnd hook)")
    ap.add_argument("--out", type=Path, default=None,
                    help="salvar Markdown em arquivo (default stdout)")
    ap.add_argument("--create-issue", action="store_true",
                    help="criar GitHub issue via gh CLI")
    ap.add_argument("--repo", type=str, default=None,
                    help="repo owner/name pra gh issue create (default: gh determina)")
    ap.add_argument("--title", type=str, default=None,
                    help="título da issue (default: auto-gerado da session)")
    args = ap.parse_args()

    if args.list:
        sessions = list_sessions(args.sessions_dir, cwd=args.cwd_filter)
        if not sessions:
            print("(no sessions found)")
            return 0
        for p in sessions:
            size = p.stat().st_size // 1024
            print(f"  {p.parent.name}/{p.stem}   {size}KB")
        return 0

    # Locate JSONL
    if args.transcript_path:
        jsonl_path = args.transcript_path
    elif args.session:
        # Search across all project dirs
        matches = list(args.sessions_dir.glob(f"*/{args.session}.jsonl"))
        if not matches:
            print(f"session not found: {args.session}", file=sys.stderr)
            return 1
        jsonl_path = matches[0]
    else:
        print("must provide --session, --transcript-path, or --list", file=sys.stderr)
        return 2

    if not jsonl_path.exists():
        print(f"jsonl not found: {jsonl_path}", file=sys.stderr)
        return 1

    print(f"parsing {jsonl_path}", file=sys.stderr)
    records = parse_jsonl(jsonl_path)
    print(f"  {len(records)} records", file=sys.stderr)

    title = args.title or f"Claude Code session — {jsonl_path.stem[:8]}"
    body = render_markdown(records, title_prefix=title)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    elif not args.create_issue:
        print(body)

    if args.create_issue:
        print(f"creating GitHub issue (repo={args.repo or 'auto'})", file=sys.stderr)
        rc = create_github_issue(title, body, repo=args.repo)
        return rc

    return 0


if __name__ == "__main__":
    sys.exit(main())
