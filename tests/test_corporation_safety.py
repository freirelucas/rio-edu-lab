"""Testes ADVERSARIAIS da segurança da corporação cibernética.

Ataca as invariantes de segurança dos workflows autônomos. Se qualquer uma
quebrar (agora ou num PR futuro), CI falha — a rede de segurança da autonomia
vira permanente, não confiança.

Invariantes testadas:
- Kill switch `CORP_ACTIVE` presente + semântica correta (off por padrão)
- concurrency (não empilha) + timeout (não roda pra sempre) em cada órgão
- Zero auto-merge (nenhum comando de merge autônomo)
- Zero LLM não-guardado em cron (regression guard pra Claude-em-CI)
- Grafo de triggers acíclico (nenhum órgão se auto-dispara)
- keepalive usa [skip ci]
- Permissões mínimas (sem write-all)

Ver docs/corporacao.md §9 (garantias anti-runaway).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WF_DIR = ROOT / ".github" / "workflows"

# Órgãos autônomos (cron-driven) que DEVEM ter o kill switch + travas.
AUTONOMOUS = ["s3star-audit", "s4-scout", "keepalive", "snowball"]
# Reativos (disparados por evento humano/CI) — travas diferentes.
REACTIVE = ["ci", "pages", "algedonic-alert"]


def _load_wf(name: str) -> dict:
    return yaml.safe_load((WF_DIR / f"{name}.yml").read_text(encoding="utf-8"))


def _wf_text(name: str) -> str:
    return (WF_DIR / f"{name}.yml").read_text(encoding="utf-8")


def _triggers(wf: dict) -> list[str]:
    # PyYAML transforma a key 'on' em bool True. Aceita ambos.
    on = wf.get(True, wf.get("on"))
    if isinstance(on, dict):
        return list(on.keys())
    if isinstance(on, list):
        return on
    return [on]


def _first_job(wf: dict) -> dict:
    return next(iter(wf["jobs"].values()))


# ─── Kill switch semântica (o coração da resposta ao "vai loopar?") ────────


def _kill_switch_allows(corp_active: str | None, event: str) -> bool:
    """Re-implementação Python da política do `if:` dos workflows:
        vars.CORP_ACTIVE == 'true' || github.event_name == 'workflow_dispatch'
    Documenta a semântica pretendida; o teste abaixo confirma que o YAML bate.
    """
    return (corp_active == "true") or (event == "workflow_dispatch")


def test_kill_switch_off_by_default_blocks_cron():
    """Sem CORP_ACTIVE (default) → cron NÃO roda. É a garantia central."""
    assert _kill_switch_allows(None, "schedule") is False
    assert _kill_switch_allows("", "schedule") is False
    assert _kill_switch_allows("false", "schedule") is False


def test_kill_switch_true_enables_cron():
    assert _kill_switch_allows("true", "schedule") is True


def test_kill_switch_manual_dispatch_always_allowed():
    """Dispatch manual sempre roda (pra testar sob demanda), mesmo off."""
    assert _kill_switch_allows(None, "workflow_dispatch") is True
    assert _kill_switch_allows("false", "workflow_dispatch") is True


def test_autonomous_workflows_have_kill_switch_in_yaml():
    """O `if:` real no YAML bate com a política testada acima."""
    for name in AUTONOMOUS:
        job = _first_job(_load_wf(name))
        cond = str(job.get("if", ""))
        assert "CORP_ACTIVE" in cond, f"{name}: sem kill switch CORP_ACTIVE"
        assert "'true'" in cond, f"{name}: kill switch não exige == 'true'"
        assert "workflow_dispatch" in cond, f"{name}: dispatch manual não isento"


# ─── Não empilha, não roda pra sempre ──────────────────────────────────────


def test_autonomous_workflows_have_concurrency():
    for name in AUTONOMOUS:
        wf = _load_wf(name)
        assert "concurrency" in wf, f"{name}: sem concurrency (pode empilhar)"
        assert wf["concurrency"].get("cancel-in-progress") is True, \
            f"{name}: concurrency não cancela run anterior"


def test_autonomous_workflows_have_timeout():
    for name in AUTONOMOUS:
        job = _first_job(_load_wf(name))
        to = job.get("timeout-minutes")
        assert isinstance(to, int) and 0 < to <= 60, \
            f"{name}: timeout ausente ou > 60min (got {to})"


# ─── Zero auto-merge (adversarial: procura comandos perigosos) ─────────────

_MERGE_PATTERNS = [
    r"gh\s+pr\s+merge",
    r"merge_pull_request",
    r"enable_pr_auto_merge",
    r"--auto\b",
    r"--admin\b",
    r"\bautomerge\b",
]


def test_no_workflow_auto_merges():
    """Nenhum workflow mergeia PR autonomamente — merge é sempre humano (S5)."""
    for wf_file in WF_DIR.glob("*.yml"):
        txt = wf_file.read_text(encoding="utf-8")
        for pat in _MERGE_PATTERNS:
            assert not re.search(pat, txt), \
                f"{wf_file.name}: contém padrão de auto-merge '{pat}'"


# ─── Zero LLM não-guardado em cron (regression guard) ──────────────────────


def test_no_unguarded_llm_in_autonomous_workflows():
    """Órgãos autônomos atuais são Python puro — zero LLM.

    Se alguém adicionar claude-code-action num cron, DEVE também adicionar
    --max-turns (cap de gasto). Este teste força essa disciplina.
    """
    for name in AUTONOMOUS:
        txt = _wf_text(name)
        if "claude-code-action" in txt or "anthropic_api_key" in txt.lower():
            assert "--max-turns" in txt, \
                f"{name}: usa Claude sem --max-turns (risco de gasto)"


# ─── Grafo de triggers acíclico (não se auto-dispara) ──────────────────────


def test_trigger_graph_no_self_loop():
    """Nenhum workflow é disparado por um evento que ele mesmo produz.

    Produtores: push (keepalive), pull_request (snowball abre PR),
    issues (audit/scout/algedonic abrem issue).
    Se um workflow PRODUZ evento X e também é DISPARADO por X → loop.
    Exceção: push com [skip ci] não dispara nada.
    """
    for wf_file in WF_DIR.glob("*.yml"):
        name = wf_file.stem
        wf = _load_wf(name)
        txt = wf_file.read_text(encoding="utf-8")
        triggers = set(_triggers(wf))

        produces = set()
        if "git push" in txt and "[skip ci]" not in txt:
            produces.add("push")
        if "create_pull_request" in txt or "peter-evans/create-pull-request" in txt:
            produces.add("pull_request")
        if "issues.create" in txt or "issue_write" in txt:
            produces.add("issues")

        overlap = produces & triggers
        assert not overlap, \
            f"{name}: SELF-LOOP — produz {overlap} e também dispara por isso"


def test_keepalive_uses_skip_ci():
    """keepalive empurra commit — DEVE usar [skip ci] pra não disparar a suíte."""
    txt = _wf_text("keepalive")
    assert "[skip ci]" in txt, "keepalive sem [skip ci] — heartbeat dispararia CI"


# ─── Permissões mínimas ────────────────────────────────────────────────────


def test_no_workflow_has_write_all_permissions():
    """Nenhum workflow pede permissão total — princípio do menor privilégio."""
    for wf_file in WF_DIR.glob("*.yml"):
        wf = yaml.safe_load(wf_file.read_text(encoding="utf-8"))
        perms = wf.get("permissions")
        if perms == "write-all":
            raise AssertionError(f"{wf_file.name}: permissions: write-all (excessivo)")


def test_autonomous_workflows_declare_explicit_permissions():
    """Cada órgão declara permissions explícitas (não herda o default amplo)."""
    for name in AUTONOMOUS:
        wf = _load_wf(name)
        assert "permissions" in wf, f"{name}: sem permissions explícitas"
        assert wf["permissions"] != "write-all"
