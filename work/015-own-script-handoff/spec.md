---
id: 015
slug: own-script-handoff
kind: spec
created: 2026-10-25
updated: 2026-10-25
---

# 015 — Write stages run the change's own script in the plugin's repo · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `ship`, `drop`, `base` or `sync`, run from a checkout on an `NNN-slug` branch whose main
   checkout `_own_repo()` accepts, where the change edited `scripts/` and the running file isn't
   that checkout's `scripts/sdlc.py`, and `SDLC_OWN_SCRIPT` is unset, reruns through that
   checkout's `scripts/sdlc.py` with the same arguments and `SDLC_OWN_SCRIPT=ran`; its output and
   exit code are the command's. Test: in a scratch plugin repo, a change whose `cmd_ship` prints a
   marker ships through its own code.
2. **R2.** No handoff when any condition in R1 fails. Tests: the change didn't touch `scripts/`;
   the running file is already the worktree's; a non-change branch; `SDLC_OWN_SCRIPT` set to any
   value (which is also what stops loops).
3. **R3.** A host never hands off. A test mirroring `test_a_host_repo_never_hands_off` (no
   manifest, another plugin's, an unreadable one).
4. **R4.** The output says which code ran: a JSON report (`base`, `sync`, `drop`) gains
   `"ran": "the change's own code"`; `ship`'s text gains a line naming the script. Tests for both.
5. **R5.** When the change's script crashes (a traceback, or `uv` failing before it runs), the
   command runs in the calling process instead, with a `⚠` line on stderr naming the crash's last
   line and saying the running copy ran: the stage is never blocked. Test: a worktree `sdlc.py`
   that raises on import.
6. **R6.** A clean refusal (non-zero exit, no traceback) is the command's own result, never
   retried with the old code. Test.
7. **R7.** `SDLC_OWN_SCRIPT=off` turns the handoff off for one command (R2's any-value rule);
   `docs/CONTRIBUTING.md` names it as the way past a change script that runs but is wrong.
8. **R8.** Close is unchanged: its `_handoff()`, `HANDOFF_ENV` and tests pass as they are. Both
   build the invocation with one shared helper (`uv run --quiet --script`, or `sys.executable`
   without `uv`).
9. **R9.** `docs/CONTRIBUTING.md`'s "When a change lands" section and `AGENTS.md`'s close paragraph
   say that in this repo the writing commands run the change's own script, and close keeps its
   own handoff.

## Design

In `main()`, after parsing and before dispatch: when `args.cmd in OWN_SCRIPT_CMDS` (`ship`,
`drop`, `base`, `sync`), `_own_script(root)`, and if it returns a script, `_run_own(script,
sys.argv[1:])`, whose exit code is returned when it ran.

`_own_script(root)`: the checkout's toplevel and branch; `DIR_RE` on the branch;
`_own_repo(main_root(root))`; the change touched `scripts/` (`git diff --quiet <merge-base main
HEAD> -- scripts` fails, or `git ls-files --others --exclude-standard -- scripts` is non-empty);
`<toplevel>/scripts/sdlc.py` differs from `Path(__file__).resolve()`; `SDLC_OWN_SCRIPT` unset.
It returns that path or None, and never raises: any git failure is no handoff.

`_run_own(script, argv)`: runs `[*_script_cmd(), str(script), *argv]` with env plus
`SDLC_OWN_SCRIPT=ran`, capturing both streams. A crash (`Traceback (most recent call last)` in
stderr, or no stdout and a non-zero exit) prints the `⚠` fallback line and returns None, so
`main()` dispatches as before. Otherwise it adds `ran` (to a JSON object on stdout, or as a line),
prints both streams, and returns the exit code.

`_script_cmd()` is shared with `_handoff()`: `[uv, "run", "--quiet", "--script"]` when `uv` is on
`PATH`, else `[sys.executable]`.

The handoff lives in the running copy, so it takes effect only once this change is on `main`:
015's own ship runs `main`'s script, which has no handoff. The first change after it that edits
`scripts/` is the first to run its own code at ship.

## Contracts touched

- **Hosts untouched.** `_own_repo()` reads the main checkout's manifest and `scripts/sdlc.py`,
  never where the script was loaded from. R3 pins it.
- **"Logic a permission rule must cover goes in the script."** The handoff is inside `sdlc.py`; no
  skill changes, no rule added, `allowed-tools` untouched.
- **Scripts called with `uv run --quiet --script`.** The rerun uses the same form, through the
  shared helper.
- **Confirm before writing.** Nothing new runs before a WAIT: the handoff only picks which code
  runs a command the skill already runs at that point.
- **Only publish pushes.** No push.
- **Close's handoff.** Untouched; separate env vars (`SDLC_CLOSE_RAN`, `SDLC_OWN_SCRIPT`), so
  neither stops or loops the other.

## Alternatives rejected

- **Refuse on a crash, as close does.** Blocks the stage on a half-built script, the risk the
  intent names; close can refuse because its rerun resumes, and these four can fall back for the
  same reason.
- **Hand off whenever the worktree's `scripts/` differs from the running copy.** Once `main` moves
  ahead, that hands off to older code.
- **Hand off every command, readers too.** More surface for nothing: the gate already runs the
  worktree's tests on its code.
- **Point `${CLAUDE_PLUGIN_ROOT}` at the worktree (`--plugin-dir`).** Works per session but has to
  be remembered, and swaps the skill text too, which is a different decision.
- **Fold close's handoff into the new one.** Risks a tested path for no saving.

## Verification

- `uv run --group dev pytest tests/test_archive.py tests/test_sdlc.py tests/test_adoption.py -q`,
  then `./check.sh`: green.
- Manual, after 015 lands: the next change that edits `scripts/` runs `sdlc.py sync` at its intent
  or spec and reports `"ran": "the change's own code"`.
