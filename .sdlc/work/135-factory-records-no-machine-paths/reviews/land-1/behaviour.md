VERDICT: PASS

No failures. The change does what its intent asks: every agent reply is marked before it is written, the home mark is `<home>`, and the one reader that depended on `~` now handles the new marks. The run's own gate record is green, and the tests I ran pass.

## Notes

- **End-to-end path.** The intent's path is a factory run, which needs a live `claude` session, so I didn't run it. The closest path I could run is the change's own test that drives `cmd_agent` with a fake agent. It plants a reply that quotes `git worktree list`, a `node` path under home, and a finding line. It then checks the builder report and the spec draft, and both file `<path-to-clone>`, `<home>` and the `CHANGE:` line intact. That test passed.
- **Probe.** I called `_placeholders()` and `is_read()` directly on a sample reply. The clone path became `<path-to-clone>`, the home path became `<home>/.nvm/bin`, `ls <home>/...` reads as a read, and a real redirect beside a mark is still a non-read.
- **Every reply is covered.** `_claude(` has one call site, in `cmd_agent`, and `_file_draft` is reached only from there. The new `_placeholders(reply, root)` sits after the failure return and before any write, so no reply bypasses it.
- **Home mark.** `HOME_MARK` is `<home>` in `factory.py` and `sdlc.py`. Both copies agree, and `test_hand_gate.py` pins them. A tracked-file grep finds no remaining code that reads `~` as the home mark. The `~/` hits left in `docs/REFERENCE.md`, `CONTRIBUTING.md` and `test_nothing_local.py` are Claude Code's own paths or the scan's own regex, and they're correct as they are.
- **Decisions.** `decisions.md` ticks D1–D3 as the assumed defaults, so I treat them as settled and don't raise them again. The builder's `decision.md` asks the person to confirm them at ship. That's the person's call at ship, not a CHANGE here.
- **Round 1 finding.** F1 (`is_read()` treating `<home>` as a redirect) is marked fixed in `findings.md`, and I confirmed the fix in the code. F2 is folded into the same fix, and `notes.md` drops it with that reason. Nothing is PREEXISTING.
- **Checks.** There is no `checks.md` in the change folder, so there are no acceptance checks for me to read.
- **Main.** The change is one commit on top of `87d0fea`. `git log HEAD..main` is empty, so main hasn't moved past this change.
- **Gate.** I read `build/round-2.gate.md` and `build/land-1.gate.md` (both `GATE: PASS`). I didn't run the gate again.

## Evidence

$ cd /Users/jafaeldon/projects-personal/sdlc/.claude/worktrees/135-factory-records-no-machine-paths && ls -la .sdlc/work/135-factory-records-no-machine-paths/ && cat .sdlc/work/135-factory-records-no-machine-paths/intent.md; ls .sdlc/work/135-factory-records-no-machine-paths/build; git log --oneline -5; git status --short | head -20
tail: `---`, `id: 135`, `tier: 1`, `stage: shipped`, `# 135 — The factory keeps this machine's paths out of every record it files`; build/: `land-1.gate.md round-1.files round-1.gate.md round-1.md round-2.files round-2.gate.md round-2.md`; log: `e75db89 The factory keeps this machine's paths out of every record it files`, `87d0fea Close 133-board-tracks-landing`; status: 3 untracked and 2 modified run files
exit: 0

$ git diff --stat 87d0fea7e2d5ca85c94703d08594ecb27ead9eab...HEAD
tail: `28 files changed, 606 insertions(+), 27 deletions(-)`
exit: 0

$ git diff 87d0fea7e2d5ca85c94703d08594ecb27ead9eab...HEAD | head -c 60000
tail: `...` (output too large to show in full; the code, test and doc parts were read separately below)
exit: 0

$ cat .sdlc/work/135-factory-records-no-machine-paths/decisions.md; cat .sdlc/work/135-factory-records-no-machine-paths/decision.md; cat .sdlc/work/135-factory-records-no-machine-paths/notes.md; cat .sdlc/work/135-factory-records-no-machine-paths/findings.md
tail: `- [x] D3 (builder round 1, default): ... → decided: the assumed default, confirmed when landing`; `DECISION: ESCALATE`; notes `- [x] pre-existing: ... → dropped: fixed by this change`; findings `## F1. [important] [correctness] ... Disposition: fixed` and `## F2. [pre-existing] ... Disposition: recorded`
exit: 0

$ git diff 87d0fea7e2d5ca85c94703d08594ecb27ead9eab...HEAD -- plugins scripts docs tests
tail: `+    command = command.replace(HOME_MARK, "HOME").replace(CLONE_MARK, "CLONE")`; `+    reply = _placeholders(reply, root)`; `+HOME_MARK = "<home>"`; `+def test_a_read_naming_a_mark_is_still_a_read()`; `+def test_every_reply_is_filed_without_this_machine_s_paths(`; `-    assert "    at <path-to-clone> under ~\n" in ours` → `+    assert "    at <path-to-clone> under <home>\n" in ours`
exit: 0

$ sed -n 3440,3510p plugins/factory/scripts/factory.py
tail: `    reply = _placeholders(reply, root)`, `    if task == "spec":`, `        return emit({**out, **_file_draft(root, folder, reply)})`, `    target.write_text(text, encoding="utf-8", newline="\n")`, `    return emit(out)`
exit: 0

$ sed -n 2398,2425p plugins/factory/scripts/factory.py
tail: `        for form in sorted(forms - {"", "/", "."}, key=len, reverse=True):`, `            text = text.replace(form, mark)`, `    return text`
exit: 0

$ git grep -n -e 'HOME_MARK' -e 'under ~' -e '"~"' -e "'~'" -e 'home directory `~`' -- ':!.sdlc/work'
tail: `plugins/factory/scripts/factory.py:244:HOME_MARK = "<home>"`, `scripts/sdlc.py:2773:HOME_MARK = "<home>"`, `tests/test_hand_gate.py:267:    assert str(repo) not in ours and f"{sdlc.HOME_MARK}/cache/venv" in ours`, `tests/test_metrics.py:1172: ... "~" not in body`
exit: 0

$ git grep -n -e '~/' -- plugins scripts tests docs | head -30
tail: `docs/REFERENCE.md:190:3. \`~/.claude/settings.json\` (\`user\`).`, `tests/test_nothing_local.py:31:    r"~/[\w-]+/",`
exit: 0

$ git grep -n -e '_claude(argv' -e '_claude(\[' -e 'def _file_draft' -e '_file_draft(' -e 'def _claude' -- plugins/factory/scripts/factory.py
tail: `plugins/factory/scripts/factory.py:2954:def _claude(argv: list[str], cwd: Path) -> tuple[int, str, str | None, dict | None]:`, `plugins/factory/scripts/factory.py:3368:def _file_draft(root: Path, folder: Path, reply: str) -> dict:`, `plugins/factory/scripts/factory.py:3475:    code, reply, problem, figures = _claude(argv, root)`, `plugins/factory/scripts/factory.py:3487:        return emit({**out, **_file_draft(root, folder, reply)})`
exit: 0

$ grep -rn "HOME_MARK\|under ~\|\"~\"\|'~'\|<home>" --include=*.py --include=*.md . | grep -v "^./.sdlc/work/" | head -40
tail: `(eval):1: no matches found: --include=*.py`
exit: 1

$ head -5 .sdlc/work/135-factory-records-no-machine-paths/build/round-2.gate.md; head -5 .sdlc/work/135-factory-records-no-machine-paths/build/land-1.gate.md
tail: `GATE: PASS`, `## Attempt 1`, `Verdict: PASS`
exit: 0

$ timeout 600000 uv run --group dev pytest -q tests/test_factory.py::test_a_read_naming_a_mark_is_still_a_read ...
tail: `zsh: command not found: timeout`
exit: 127

$ uv run --group dev pytest -q tests/test_factory.py::test_a_read_naming_a_mark_is_still_a_read tests/test_factory.py::test_the_gate_records_no_path_of_this_machine tests/test_factory.py::test_a_path_under_home_is_filed_in_a_form_the_scan_accepts tests/test_factory.py::test_every_reply_is_filed_without_this_machine_s_paths tests/test_hand_gate.py tests/test_nothing_local.py 2>&1 | tail -25
tail: `47 passed in 12.63s` (the pipe hid the exit code; the summary has no failure, and the run below captured its exit)
exit: 0

$ uv run --group dev pytest -q -p no:cacheprovider tests/test_factory.py tests/test_hand_gate.py tests/test_nothing_local.py > /tmp/135-pytest.txt 2>&1; tail -5 /tmp/135-pytest.txt
tail: `323 passed in 69.18s (0:01:09)`
exit: 0

$ python3 -I -c '<probe: import factory.py by path; _placeholders() on a sample reply; is_read() on mark commands>'
tail: `$ ls <home>/.nvm/bin` / `node` / `is_read ls mark: True | redirect still non-read: False`
exit: 0

$ git -C . rev-parse --short 87d0fea; git log --oneline 87d0fea..HEAD --no-merges; git log --oneline HEAD..main
tail: `87d0fea`, `e75db89 The factory keeps this machine's paths out of every record it files` (`HEAD..main` empty)
exit: 0
