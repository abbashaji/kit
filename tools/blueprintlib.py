"""blueprintlib: shared graph logic for the cell blueprint (stdlib + PyYAML).

Cells are immutable YAML files in cells/. Status is never stored: it is computed from git
(merged = a "cell(C-NNN):" commit on main, running = a branch cell/C-NNN with a live lease).
"""
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

import yaml

ID_RE = re.compile(r"^C-\d{3,}$")
SUBJECT_RE = re.compile(r"^cell\((C-\d{3,})\)")
BRANCH_RE = re.compile(r"^cell/(C-\d{3,})$")
KINDS = ("implementation", "contract")
CELL_TYPES = ("normal", "skeleton", "integration")
DEFAULT_PROTECTED = [
    "cells/**", "blueprint.yaml", "BLUEPRINT.md", "tools/**",
    ".github/**", "acceptance/**", "docs/decisions.md",
]
DEFAULTS = {
    "main_branch": "main",
    "lease_minutes": 60,          # default; a cell can override with its own lease_minutes
    "max_ci_minutes": 45,         # a running workflow keeps a lease alive at most this long
    "bottleneck_threshold": 4,    # cells directly blocking this many others are flagged
    "max_cell_files": 8,
    "acceptance_timeout_s": 600,
    "protected_paths": [],
    "owners": {},
}


# ---------------------------------------------------------------- loading
def load_config(root) -> dict:
    cfg = dict(DEFAULTS)
    p = Path(root) / "blueprint.yaml"
    if p.exists():
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        cfg.update({k: v for k, v in data.items() if k in DEFAULTS or k == "project"})
    cfg["protected_paths"] = DEFAULT_PROTECTED + list(cfg.get("protected_paths") or [])
    cfg["owners"] = dict(cfg.get("owners") or {})
    return cfg


def load_cells(cells_dir):
    """Return ({id: cell}, [load errors])."""
    cells, errors = {}, []
    d = Path(cells_dir)
    if not d.is_dir():
        return {}, [f"{d}: cells directory not found"]
    for f in sorted(d.glob("C-*.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            errors.append(f"{f.name}: invalid YAML ({str(e).splitlines()[0]})")
            continue
        if not isinstance(data, dict):
            errors.append(f"{f.name}: must be a mapping")
            continue
        if data.get("id") != f.stem:
            errors.append(f"{f.name}: id {data.get('id')!r} must equal file name {f.stem!r}")
        data["id"] = f.stem
        cells[f.stem] = data
    return cells, errors


def slist(cell, key):
    v = cell.get(key)
    return [x for x in v if isinstance(x, str)] if isinstance(v, list) else []


def inputs_of(cell):
    return [i for i in (cell.get("inputs") or []) if isinstance(i, dict)]


def hard_deps(cell):
    """Cells that must be MERGED before this one may start."""
    deps = [i.get("from") for i in inputs_of(cell) if i.get("kind") == "implementation"]
    deps += slist(cell, "after")
    out = []
    for d in deps:
        if isinstance(d, str) and d not in out:
            out.append(d)
    return out


def acceptance_cmds(cell):
    out = []
    for a in cell.get("acceptance") or []:
        if isinstance(a, str) and a.strip():
            out.append(a.strip())
        elif isinstance(a, dict) and isinstance(a.get("cmd"), str) and a["cmd"].strip():
            out.append(a["cmd"].strip())
    return out


# ---------------------------------------------------------------- paths
def _norm(p: str) -> str:
    p = re.sub(r"^\./", "", p.strip())
    return p + "**" if p.endswith("/") else p


def _has_wild(s: str) -> bool:
    return any(ch in s for ch in "*?[")


def glob_regex(pat: str):
    pat = _norm(pat)
    i, out = 0, ""
    while i < len(pat):
        if pat.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pat.startswith("**", i):
            out += ".*"
            i += 2
        elif pat[i] == "*":
            out += "[^/]*"
            i += 1
        elif pat[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pat[i])
            i += 1
    return re.compile("^" + out + "$")


def matches(path: str, patterns) -> bool:
    return any(glob_regex(p).match(path) for p in patterns)


def may_overlap(a: str, b: str) -> bool:
    """Conservative: True if some path could match both globs.

    Entries ending in '/' or '/**' are directories. An exact entry without wildcards is a file.
    """
    A, B = _norm(a).split("/"), _norm(b).split("/")
    for x, y in zip(A, B):
        if x == "**" or y == "**":
            return True
        wx, wy = _has_wild(x), _has_wild(y)
        if not wx and not wy:
            if x != y:
                return False
        elif wx and wy:
            continue  # two different wildcards: cannot rule out, stay conservative
        elif not (fnmatch.fnmatchcase(x, y) or fnmatch.fnmatchcase(y, x)):
            return False
    return len(A) == len(B)


def first_overlap(paths_a, paths_b):
    for pa in paths_a:
        for pb in paths_b:
            if may_overlap(pa, pb):
                return pa, pb
    return None


# ---------------------------------------------------------------- graph
def find_cycle(graph):
    color = {n: 0 for n in graph}
    stack = []

    def dfs(n):
        color[n] = 1
        stack.append(n)
        for m in graph[n]:
            if color[m] == 1:
                return stack[stack.index(m):] + [m]
            if color[m] == 0:
                r = dfs(m)
                if r:
                    return r
        stack.pop()
        color[n] = 2
        return None

    for n in graph:
        if color[n] == 0:
            r = dfs(n)
            if r:
                return r
    return None


def ancestors(graph):
    memo = {}

    def f(n):
        if n not in memo:
            s = set()
            for d in graph[n]:
                s.add(d)
                s |= f(d)
            memo[n] = s
        return memo[n]

    return {n: f(n) for n in graph}


def hard_graph(cells):
    ids = set(cells)
    return {cid: [d for d in hard_deps(c) if d in ids and d != cid] for cid, c in cells.items()}


def waves(cells):
    """Topological levels over hard edges: {level: [ids]}. Cells in one level can run in parallel."""
    g = hard_graph(cells)
    level = {}

    def lv(n):
        if n not in level:
            level[n] = 1 + max((lv(d) for d in g[n]), default=-1)
        return level[n]

    out = {}
    for n in g:
        out.setdefault(lv(n), []).append(n)
    return {k: sorted(v) for k, v in sorted(out.items())}


# ---------------------------------------------------------------- validation
def validate(cells, cfg):
    """Return (errors, warnings)."""
    E, W = [], []
    ids = set(cells)
    if not cells:
        E.append("no cells found")
    protected = cfg["protected_paths"]

    for cid, c in cells.items():
        p = f"{cid}: "
        if not ID_RE.match(cid):
            E.append(p + "id must look like C-001")
        for k in ("title", "goal", "allowed_paths", "outputs", "acceptance"):
            if not c.get(k):
                E.append(p + f"missing '{k}'")
        for k in ("allowed_paths", "outputs", "after", "provides", "read"):
            v = c.get(k)
            if v is not None and not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
                E.append(p + f"'{k}' must be a list of strings")
        t = c.get("type", "normal")
        if t not in CELL_TYPES:
            E.append(p + f"type must be one of {CELL_TYPES}")
        if "priority" in c and not isinstance(c["priority"], int):
            E.append(p + "priority must be an integer")
        if "lease_minutes" in c and not (isinstance(c["lease_minutes"], int) and not isinstance(c["lease_minutes"], bool)
                                         and c["lease_minutes"] > 0):
            E.append(p + "lease_minutes must be a positive integer")
        if c.get("acceptance") and not acceptance_cmds(c):
            E.append(p + "acceptance needs at least one command ('cmd: ...')")

        for n, i in enumerate(c.get("inputs") or []):
            q = p + f"inputs[{n}]: "
            if not isinstance(i, dict):
                E.append(q + "must be a mapping")
                continue
            src, kind = i.get("from"), i.get("kind")
            if src not in ids:
                E.append(q + f"unknown cell {src!r}")
            elif src == cid:
                E.append(q + "a cell cannot depend on itself")
            if kind not in KINDS:
                E.append(q + f"kind must be one of {KINDS}")
            if not str(i.get("contract") or "").strip():
                E.append(q + "contract text required (the agent must not need to read the provider's code)")
            if kind == "contract" and src in ids and src != cid and not slist(cells[src], "provides"):
                E.append(q + f"{src} has no 'provides' to consume as a contract")
        for a in slist(c, "after"):
            if a not in ids:
                E.append(p + f"after: unknown cell {a!r}")
            elif a == cid:
                E.append(p + "after: a cell cannot depend on itself")

        allowed, outputs = slist(c, "allowed_paths"), slist(c, "outputs")
        if len(outputs) > cfg["max_cell_files"]:
            E.append(p + f"{len(outputs)} outputs exceeds max_cell_files={cfg['max_cell_files']} (split the cell)")
        for o in outputs:
            if _has_wild(o) or o.endswith("/"):
                E.append(p + f"output {o!r} must be a concrete file path")
            elif not matches(o, allowed):
                E.append(p + f"output {o!r} is not covered by allowed_paths")
        for ap in allowed:
            hit = next((q_ for q_ in protected if may_overlap(ap, q_)), None)
            if hit:
                E.append(p + f"allowed path {ap!r} touches protected path {hit!r}")
        for glob, owner in cfg["owners"].items():
            if owner not in ids:
                E.append(f"blueprint.yaml owners: {glob!r} is owned by unknown cell {owner!r}")
            elif cid != owner and any(may_overlap(ap, glob) for ap in allowed):
                E.append(p + f"touches {glob!r}, which is owned by {owner}")

    graph = hard_graph(cells)
    cyc = find_cycle(graph) if graph else None
    if cyc:
        E.append("dependency cycle: " + " -> ".join(cyc))
        return E, W

    anc = ancestors(graph)
    order = sorted(cells)
    for ia, a in enumerate(order):
        for b in order[ia + 1:]:
            if a in anc[b] or b in anc[a]:
                continue  # ordered by dependencies: may share paths
            hit = first_overlap(slist(cells[a], "allowed_paths"), slist(cells[b], "allowed_paths"))
            if hit:
                E.append(f"{a} and {b} can run in parallel but their paths overlap: {hit[0]} ~ {hit[1]} "
                         "(add an 'after' edge or split the paths)")

    integrations = [i for i, c in cells.items() if c.get("type") == "integration"]
    for cid, c in cells.items():
        for i in inputs_of(c):
            if i.get("kind") == "contract" and i.get("from") in ids:
                prov = i["from"]
                if not any(cid in anc[x] and prov in anc[x] for x in integrations):
                    W.append(f"{cid} uses a contract of {prov} but no integration cell depends on both "
                             "(real wiring would go untested)")

    for cid, n in sorted(direct_dependents(cells).items()):
        if n >= cfg.get("bottleneck_threshold", DEFAULTS["bottleneck_threshold"]) and cells[cid].get("type") != "skeleton":
            W.append(f"{cid} is a bottleneck: {n} cells wait for it to be merged. Turn some of those inputs into "
                     "kind: contract, split it, or give it a short lease_minutes and top priority")
    return E, W


def direct_dependents(cells):
    """{cell id: number of cells that must wait for its MERGE (implementation / after edges)}."""
    out = {c: 0 for c in cells}
    for deps in hard_graph(cells).values():
        for d in deps:
            out[d] += 1
    return out


# ---------------------------------------------------------------- readiness
def lease_of(cell, default):
    v = cell.get("lease_minutes")
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 0 else default


def compute_state(cells, merged, claims, lease_minutes=60, ci=None, max_ci_minutes=45, bottleneck_threshold=4):
    """Decide what can be started.

    merged: set of merged cell ids.
    claims: {id: minutes since the last commit on that cell's branch}.
    ci:     {id: minutes since the NEWEST still-active workflow run for that cell started}.

    A claimed cell stays locked while its commit lease is alive OR a workflow run for it is active, so a chat
    that is only waiting for CI is not mistaken for a dead one. A run counts for at most max_ci_minutes,
    so a hung run cannot hold a cell forever. The lease is per cell (lease_minutes) with a project default.
    """
    ci = ci or {}
    merged = set(merged) & set(cells)
    todo = [c for c in cells if c not in merged]
    if not todo:
        return {"status": "all_done", "ready": [], "locked": [], "waiting": []}

    direct = direct_dependents(cells)

    def critical(cid):
        return direct[cid] >= bottleneck_threshold and cells[cid].get("type") != "skeleton"

    graph = hard_graph(cells)
    dependents = {c: [] for c in cells}
    for c, ds in graph.items():
        for d in ds:
            dependents[d].append(c)
    depth = {}

    def dp(n):
        if n not in depth:
            depth[n] = 1 + max((dp(x) for x in dependents[n]), default=0)
        return depth[n]

    ready, locked, waiting = [], [], []
    for cid in todo:
        blockers = [d for d in graph[cid] if d not in merged]
        if blockers:
            waiting.append({"id": cid, "blocked_by": blockers})
            continue
        age = claims.get(cid)
        lease = lease_of(cells[cid], lease_minutes)
        if age is not None and age < lease:
            locked.append({"id": cid, "minutes_left": round(lease - age)})
        elif age is not None and cid in ci and ci[cid] < max_ci_minutes:
            locked.append({"id": cid, "minutes_left": round(max_ci_minutes - ci[cid]), "ci": True})
        else:
            ready.append({"id": cid, "reclaim": age is not None, "critical": critical(cid)})
    ready.sort(key=lambda r: (not r["reclaim"], -int(cells[r["id"]].get("priority") or 0), -dp(r["id"]), r["id"]))
    return {"status": "ready" if ready else "none_ready", "ready": ready, "locked": locked, "waiting": waiting}


def render(state, max_waiting=8) -> str:
    """Compact text for an agent: a few dozen tokens."""
    if state["status"] == "all_done":
        return "ALL_DONE: every cell is merged."
    if state["status"] == "ready":
        names = " ".join(r["id"] + ("[critical]" if r.get("critical") else "")
                         + ("(expired-lease)" if r["reclaim"] else "") for r in state["ready"])
        return f"READY {names}\n(take the first)"
    lines = ["NONE_READY: no cell can be started now."]
    if state["locked"]:
        lines.append("running: " + ", ".join(
            f"{x['id']}(CI<={x['minutes_left']}m)" if x.get("ci") else f"{x['id']}({x['minutes_left']}m)"
            for x in state["locked"]))
    w = state["waiting"]
    if w:
        shown = "; ".join(f"{x['id']}<-{','.join(x['blocked_by'])}" for x in w[:max_waiting])
        lines.append("waiting: " + shown + (f"; +{len(w) - max_waiting} more" if len(w) > max_waiting else ""))
    lines.append("Wait for the running cells to merge, then ask again.")
    return "\n".join(lines)


# ---------------------------------------------------------------- git state
def git(root, *args, check=True):
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def merged_from_git(root, ref):
    out = git(root, "log", ref, "--format=%s")
    return {m.group(1) for line in out.splitlines() if (m := SUBJECT_RE.match(line))}


ACTIVE_RUN = {"queued", "in_progress", "waiting", "pending", "requested"}
RUN_TITLE_RE = re.compile(r"\b(?:gate|preflight)\s+(?:cell/)?(C-\d{3,})\b")


def parse_runs(runs, now=None):
    """Turn `gh run list --json status,headBranch,displayTitle,createdAt` into {cell id: minutes since the
    NEWEST active run started}. The cell id comes from the head branch (cell/C-NNN) or from the run title
    ("gate cell/C-NNN" / "preflight C-NNN", set with run-name: in the workflows). The title is the reliable
    source: pull_request_target and workflow_dispatch runs belong to the base branch, not the cell branch."""
    now = time.time() if now is None else now
    out = {}
    for r in runs or []:
        if r.get("status") not in ACTIVE_RUN:
            continue
        m = BRANCH_RE.match(r.get("headBranch") or "") or RUN_TITLE_RE.search(r.get("displayTitle") or "")
        if not m:
            continue
        try:
            started = datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00")).timestamp()
        except (KeyError, ValueError, AttributeError):
            continue
        age = max(0.0, (now - started) / 60)
        cid = m.group(1)
        out[cid] = min(out.get(cid, age), age)
    return out


def ci_from_gh(repo=None, now=None, limit=100):
    """Active-run signal from the GitHub CLI. Returns None when it cannot be read (gh missing, no auth)."""
    cmd = ["gh", "run", "list", "--json", "status,headBranch,displayTitle,createdAt", "--limit", str(limit)]
    if repo:
        cmd += ["--repo", repo]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return None
        return parse_runs(json.loads(r.stdout), now)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def claims_from_git(root, remote="origin", now=None):
    now = time.time() if now is None else now
    out = git(root, "for-each-ref", f"refs/remotes/{remote}/cell/",
              "--format=%(refname:strip=3) %(committerdate:unix)")
    claims = {}
    for line in out.splitlines():
        name, ts = line.rsplit(" ", 1)
        m = BRANCH_RE.match(name)
        if m:
            claims[m.group(1)] = max(0.0, (now - int(ts)) / 60)
    return claims
