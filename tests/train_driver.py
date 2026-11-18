"""One driver for a landing train, as the land skill took its steps before `train --run`: each
reading's step done by the command it names, in process, agents stood in for by files.

It takes the `factory` module as an argument, since each test file loads `factory.py` by path
under a name of its own. `tests/test_train.py` and `tests/test_land.py` both drive trains with it
(147 R15); `train --run` can't be the tests' driver, since a monkeypatch can't reach the agents it
starts in subprocesses.

It also holds the stand-in `claude` the loop's tests put on `PATH` (`fake_claude()`), which
answers each agent by its name and the change whose worktree it runs in.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Every `next` a reading names that the driver takes, `done` and `stop` included.
DRIVER_STEPS = frozenset(
    {"commit", "stack", "resolve", "gate", "eject", "accept", "review", "verify", "mend", "fix",
     "close", "stop", "done"}
)  # fmt: skip


def _run(capsys, fn, *args, **kwargs) -> tuple[int, dict]:
    capsys.readouterr()
    code = fn(*args, **kwargs)
    return code, json.loads(capsys.readouterr().out)


def folder_of(tree: Path) -> Path:
    return tree / ".sdlc" / "work" / tree.name


def verdict(factory, role: str, says: str = "PASS", changes: tuple[str, ...] = ()) -> str:
    """A reviewer's reply: its verdict, its changes, and `## Evidence` for a role that runs the
    change."""
    lines = [f"VERDICT: {says}", *(f"- CHANGE: {c}" for c in changes)]
    evidence = "\n## Evidence\n$ true\nexit: 0\n" if role in factory.RUNS_THE_CHANGE else ""
    return "\n".join(lines) + "\n" + evidence


def verified(factory, folder: Path, n: int, kept=(), dropped=()) -> None:
    """The verifier's answers, each `<role>: <change>` as the reviewer asked it."""
    lines = [f"- KEPT: {c}" for c in kept] + [f"- DROPPED: {c}" for c in dropped]
    (folder / "reviews" / f"land-{n}" / factory.VERIFIED).write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def asked(found: dict) -> list[str]:
    """Every change a landing round's reviewers asked for, as `<role>: <change>`."""
    return [
        f"{role}: {c}" for role, r in found["reviews"].items()
        if r["verdict"] == "CHANGES" for c in r["changes"]
    ]  # fmt: skip


def drive_train(
    factory,
    root: Path,
    capsys,
    begin: list[Path] | None = None,
    by: str = "auto",
    resolve=None,
    review=None,
    verify=None,
    mend=None,
    fix=None,
    strict: bool = False,
    limit: int = 80,
    until=None,
) -> list[dict]:
    """Run the train as the land skill did, step by step, in process. With `begin`, first begin
    one over those worktrees' changes `by` auto or person, unless one is under way.
    `resolve(tree, files)` writes a resolution; `review(folder, n, role)` a verdict (PASS by
    default); `verify(folder, verdict)` the verifier's answer (every change dropped by default);
    `mend(folder, n, role)` the role's reply again (a passing one by default), recorded in
    `runs/mended` as `agent --task land-mend` records it; `fix(tree)` the builder's edit for a
    stored fix, between `land-fix --ask` and `--commit`. A `commit` runs what the reading says
    comes `before` it (`accept`, `cases`); an `eject` runs `--eject` whatever its cause. With
    `strict`, every gate must pass, no stack may conflict, a close must merge and a `stop` is a
    failure. Stops at `done`, at `stop` (after `--stop`), or once `until(reading)` holds. Returns
    every reading, an `eject`'s with what `--eject` printed as `did`."""
    if begin is not None and factory.read_train(root) is None:
        code, out = _run(capsys, factory.cmd_train, root, begin=[t.name for t in begin], by=by)
        assert code == 0 and out["state"] == "begun", out
    readings: list[dict] = []
    for _ in range(limit):
        code, out = _run(capsys, factory.cmd_train, root)
        readings.append(out)
        nxt = out.get("next")
        if until is not None and until(out):
            return readings
        if nxt in (None, "done"):
            return readings
        if nxt == "stop":
            assert not strict, out
            code, stopped = _run(capsys, factory.cmd_train, root, stop=True)
            assert code == 0, stopped
            readings.append(stopped)
            return readings
        tree, num = Path(out["worktree"]), out["change"].split("-")[0]
        folder = folder_of(tree)
        if nxt == "commit":
            for first in out["before"]:
                assert _run(capsys, getattr(factory, f"cmd_{first}"), tree, num)[0] == 0
            code, done = _run(capsys, factory.cmd_land, tree, num, out["by"])
            assert code == 0, done
        elif nxt == "stack":
            code, done = _run(capsys, factory.cmd_resolve, tree, num, False, onto=out["onto"])
            states = ("current", "stacked") if strict else ("current", "stacked", "conflict")
            assert code == 0 and done["state"] in states, done
        elif nxt == "resolve":
            assert resolve is not None, out
            resolve(tree, out["files"])
            code, done = _run(capsys, factory.cmd_resolve, tree, num, True)
            assert code == 0, done
        elif nxt == "gate":
            code, done = _run(capsys, factory.cmd_gate, tree, num, True)
            assert not strict or done["verdict"] == "PASS", done
        elif nxt == "eject":
            code, done = _run(capsys, factory.cmd_train, root, eject=out["change"])
            assert code == 0, done
            out["did"] = done
        elif nxt == "accept":
            code, done = _run(capsys, factory.cmd_accept, tree, num)
            assert not strict or code == 0, done
        elif nxt == "review":
            n = out["verdict"]["round"]
            for role in out["verdict"]["missing"]:
                if review is not None:
                    review(folder, n, role)
                else:
                    reply = folder / "reviews" / f"land-{n}" / f"{role}.md"
                    reply.write_text(verdict(factory, role), encoding="utf-8")
        elif nxt == "verify":
            if verify is not None:
                verify(folder, out["verdict"])
            else:
                verified(factory, folder, out["verdict"]["round"], dropped=asked(out["verdict"]))
        elif nxt == "mend":
            n = out["verdict"]["round"]
            for role in out["verdict"]["mend"]:
                if mend is not None:
                    mend(folder, n, role)
                else:
                    reply = folder / "reviews" / f"land-{n}" / f"{role}.md"
                    reply.write_text(verdict(factory, role), encoding="utf-8")
                with (folder / factory.MENDED).open("a", encoding="utf-8") as f:
                    f.write(f"{role} land-{n}\n")
        elif nxt == "fix":
            assert fix is not None, out
            if not out["asked"]:
                code, done = _run(capsys, factory.cmd_land_fix, tree, num, out["ask"], False)
                assert code == 0, done
            fix(tree)
            code, done = _run(capsys, factory.cmd_land_fix, tree, num, None, True)
            assert code == 0, done
        elif nxt == "close":
            code, done = _run(capsys, factory.cmd_land_close, tree, num)
            assert code == 0, done
            assert not strict or "merge" in done.get("done", []) or done.get("state") == "moved"
        else:
            raise AssertionError(f"the driver can't take the step {nxt!r}: {out}")
    raise AssertionError(f"the train didn't finish in {limit} steps: {readings[-1]}")


# ---------------------------------------------------------------- a stand-in `claude` on PATH

FAKE_CLAUDE = """\
#!/usr/bin/env python3
import json, os, subprocess, sys, time
from pathlib import Path

argv = sys.argv[1:]
agent = argv[argv.index("--agent") + 1].split(":")[-1]
cwd = Path.cwd()
plan = json.loads(Path(os.environ["TRAIN_AGENTS"]).read_text(encoding="utf-8"))
start = time.time()
entry = plan.get(f"{cwd.name}:{agent}") or plan.get(agent) or {}
for path, text in (entry.get("write") or {}).items():
    (cwd / path).parent.mkdir(parents=True, exist_ok=True)
    (cwd / path).write_text(text, encoding="utf-8")
if entry.get("block"):
    flag = Path(entry["block"])
    if not flag.exists():
        flag.write_text("blocking\\n", encoding="utf-8")
        Path(entry["block"] + ".started").write_text("started\\n", encoding="utf-8")
        while True:
            time.sleep(0.2)
time.sleep(entry.get("sleep", 0))
if entry.get("run"):
    subprocess.run(entry["run"], cwd=cwd, capture_output=True)
with open(os.environ["TRAIN_AGENTS_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"agent": agent, "change": cwd.name, "start": start, "end": time.time(),
                        "prompt": argv[argv.index("-p") + 1]}) + "\\n")
reply = entry.get("reply")
if reply is None:
    if agent.startswith("reviewer-"):
        reply = "VERDICT: PASS\\n\\n## Evidence\\n$ true\\nexit: 0\\n"
    elif agent == "verifier":
        reply = "- DROPPED: nothing: nothing asked\\n"
    else:
        reply = "Done.\\n\\n## Evidence\\n\\n$ true\\nexit: 0\\n"
print(json.dumps({"type": "system", "subtype": "init", "session_id": "s"}))
print(json.dumps({"type": "assistant",
                  "message": {"role": "assistant", "content": [{"type": "text", "text": reply}]}}))
print(json.dumps({"type": "result", "is_error": False, "result": reply}))
"""


def fake_claude(tmp_path: Path, monkeypatch, plan: dict | None = None):
    """A stand-in `claude` on PATH for the agents `train --run` starts. `plan` maps
    `<change>:<agent>` or `<agent>` (`reviewer-behaviour`, `verifier`, `builder`) to what it
    does: `reply`, its text (a passing one by default); `write`, files to write in its worktree;
    `sleep`, seconds; `run`, a command (an argv) to run before it replies; `block`, a flag file:
    the first call writes it and `<flag>.started`, then waits for good. Returns a reader of the
    calls it finished, each with `agent`, `change`, `start`, `end` and `prompt`."""
    bin_dir = tmp_path / "claude-bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "claude").write_text(FAKE_CLAUDE, encoding="utf-8")
    (bin_dir / "claude").chmod(0o755)
    (tmp_path / "agents.json").write_text(json.dumps(plan or {}), encoding="utf-8")
    log = tmp_path / "agents.jsonl"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("TRAIN_AGENTS", str(tmp_path / "agents.json"))
    monkeypatch.setenv("TRAIN_AGENTS_LOG", str(log))

    def calls() -> list[dict]:
        if not log.exists():
            return []
        return [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()]

    return calls
