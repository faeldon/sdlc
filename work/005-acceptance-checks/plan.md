---
id: 005
slug: acceptance-checks
kind: plan
created: 2026-10-24
updated: 2026-10-24
---

# 005 — Rerun a change's acceptance checks at ship · plan

> Produced by Claude Code **plan mode**, then saved here once you approve it. Don't hand-write
> this — the value is that Claude read the codebase first. Copy the approved plan
> from ~/.claude/plans/ and trim it to the sections below.

## Context

Stage 4 records an acceptance check, one that only a deliberate revert could fail, as prose in
`notes.md`. By `/sdlc:ship`, review fixes or a rebase may have changed what it checked, and
nothing reruns it. The spec (`work/005-acceptance-checks/spec.md`, R1–R7) has a change keep its
checks in `work/NNN-slug/checks.md`, one `## ` section per check with one `sh` block. Ship lists
them, read-only, then runs them through `sdlc.py accept <NNN>`, which deliberately has no allow
rule, so the person gets one prompt with the commands in view. The branch is already on `main`
at `dbe7a90`, which includes 004's base step.

## Files to change

- `templates/checks.md` (new): `# Checks`, the `>` note, one example section (spec R1).
- `scripts/sdlc.py`:
  - `"checks.md"` in `DOC_TEMPLATES`, and after `notes.md` in `ARTIFACT_ORDER`;
  - `SH_FENCE_RE`;
  - `acceptance(folder)` beside `open_items()`;
  - its problems in `analyze()`;
  - `cmd_checks` and `cmd_accept` beside `cmd_undone`;
  - `"checks"` in `READ_ONLY`, so it joins `ALLOW_RULES`;
  - two argparse entries and their dispatch.
- `skills/ship/SKILL.md`:
  - Step 1 gains the checks paragraph after the gate;
  - Step 7 reports each check;
  - one new `allowed-tools` rule, for `sdlc.py checks *` only.
- `defaults/SDLC.md`, `.sdlc/SDLC.md`: Stage 4's Acceptance bullet, identical in both.
- `defaults/REVIEW.md`, `.sdlc/REVIEW.md`: Pass 1's opening clause and **A test only a revert can
  fail.**, word for word in both.
- `plugins/factory/agents/reviewer-test.md`: **How each test could fail.** asks for `checks.md`
  and runs each check's block itself.
- `plugins/factory/agents/builder.md`: a short **Acceptance checks** paragraph in the build loop,
  embedding `templates/checks.md` verbatim as the text to start from.
- `docs/REFERENCE.md`: `checks.md` in `## work/ and worktrees` and in the templates list; ship's
  checks in its description.
- `AGENTS.md`: one sentence in the architecture map, under *Tiers and stages* or the ship context
  paragraph: checks are listed by `checks`, run by `accept`, and `accept` never gets a rule.
- `.sdlc/setup.json`: re-recorded with `sdlc.py record`.
- `tests/test_acceptance.py` (new): R1–R4.
- `tests/test_skills.py`: R5's placement test, and the no-rule-for-`accept` test across every
  skill.
- `tests/test_readiness.py`: `"accept"` added to the writers that must not be allowed.
- `tests/test_defaults.py`: builder.md carries `templates/checks.md` verbatim (like the
  `NOTES_HEAD` test).
- `work/005-acceptance-checks/checks.md` (new): this change's own checks (R7).

## Work order

1. **Template and parser (R1, R2).**
   - Write `templates/checks.md`. Run `pytest tests/test_defaults.py`; the one-shape tests pick it
     up by glob.
   - `acceptance(folder) -> {"path", "exists", "checks": [{"name", "command"}], "problems"}`:
     - no file: `exists: False`, nothing else;
     - `is_unfilled(path)`: one problem, `checks.md is still the template: fill it or delete it`;
     - otherwise walk the lines with `FENCE_RE`, splitting at `## ` outside fences. In each
       section, collect fenced blocks whose opening line matches
       `SH_FENCE_RE = re.compile(r"^\s*(```|~~~)\s*sh\s*$")`; other fences, such as expected
       output, are ignored;
     - problems: a section with no `sh` block, a section with more than one, a duplicate name, and
       text before the first `##` that holds an `sh` block;
     - read errors (`OSError`, `UnicodeDecodeError`) become a problem, never a raise.
   - In `analyze()`'s problem loop, for each non-dropped change, add each `acceptance()` problem
     as `{"dir", "kind": "checks", "detail"}`, so `check --strict` reports it.
   - Tests: no file, the template itself is unfilled, a good file, and one test per problem.
2. **List and run (R3, R4).**
   - `cmd_checks(root, ident)` uses `_one_change()` and prints `acceptance()` plus `change`.
     Exit 0, or 1 when there are problems. It writes nothing.
   - `cmd_accept(root, ident)`:
     - `checkout = folder.parent.parent`;
     - `before = git status --porcelain` there;
     - for each check, `subprocess.run(["sh", "-c", cmd], cwd=checkout, capture_output=True,
       text=True, timeout=300)`, recording `exit` (None on timeout), `passed`, `seconds`, and
       `output`: the last 40 lines of stdout and stderr;
     - after each check, compare the status lines with `before`. New or changed lines fail that
       check, with `left: [...]`;
     - print `{"change", "checks", "passed", "problems"}`. Exit 1 on any failure or problem, and 0
       with no checks (`"checks": []`, `passed: true`).
   - `READ_ONLY` gains `"checks"` only.
   - Tests:
     - a pass, a fail (exit 3), and a timeout (patch the timeout down to 1 with
       `monkeypatch.setattr` on a module constant `CHECK_TIMEOUT`);
     - a check that writes a file fails, naming it;
     - no file exits 0, and a bad file exits 1;
     - it runs from the checkout root (`pwd` in the output);
     - `accept` is not in `ALLOW_RULES`; `checks` is.
3. **Ship (R5).**
   - Edit Step 1 after the gate paragraph:
     - a bash block with `sdlc.py checks <NNN>`;
     - prose: when it lists any, show each name and command, then run `sdlc.py accept <NNN>`,
       named in prose only, with no rule, so the harness asks with the list in view;
     - a failure stops here, with each failing check's name and output, and `left`;
     - with none, one line: "no acceptance checks".
   - Step 7: "each acceptance check by name and its result".
   - Add the rule `'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py checks *)'`.
   - Tests in `test_skills.py`:
     - `test_ship_lists_then_runs_the_changes_checks_under_a_prompt`: in Step 1, the gate text,
       then `sdlc.py checks <NNN>`, then `sdlc.py accept <NNN>`, in that order, all before
       `## Step 2`;
     - `test_no_skill_lets_accept_run_unasked`: no rule in any skill (factory included) matches
       `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py accept 005` under
       `_rule_regex`;
     - `test_readiness.py`'s writer tuple gains `"accept"`.
4. **Docs (R6).**
   - Stage 4 Acceptance bullet (both copies): "…Write it as a `## ` section of the change's
     `checks.md` (`templates/checks.md`), one `sh` block that exits 0 while the outcome holds;
     `/sdlc:ship` reruns it before it commits. One that can't run, such as looking at a rendered
     page, is recorded in `notes.md`: what was done and what it showed. Either way it reaches
     history with the folder and stays out of the suite, …"
   - Review Pass 1 (both copies):
     - the opening clause becomes "…unless only a revert could fail it and the change's
       `checks.md` holds the check that proves it (`notes.md` when it can't run)";
     - the bullet ends "…so it is an acceptance check, kept in the change's `checks.md` (or
       `notes.md` when it can't run)."
   - reviewer-test.md: "…ask for it as a section of `checks.md` instead of a test in the suite,
     and run each section's `sh` block yourself; a requirement proved that way is covered."
   - builder.md: a paragraph saying where an acceptance-only requirement's proof goes, with the
     template text in a fenced block. A test asserts `templates/checks.md`'s text appears in
     builder.md.
   - REFERENCE, AGENTS.
   - Run `sdlc.py record` and check that `sdlc.py drift` reports nothing.
5. **Dogfood (R7) and gate.**
   - Write `work/005-acceptance-checks/checks.md` with three checks:
     - `uv run --quiet --script scripts/sdlc.py config` lists `checks.md` under `templates`;
     - Stage 4 in both SDLC docs points acceptance at `checks.md`;
     - the factory's test reviewer asks for `checks.md`, and no longer for a record in `notes.md`.
   - Run `sdlc.py checks 005`, then `sdlc.py accept 005`, and see each pass with the tree
     unchanged.
   - Run `./check.sh`.

## Tests

- **R1:** the one-shape tests over `templates/checks.md` (by glob);
  `test_config_lists_the_checks_template`; `test_builder_starts_checks_from_the_template`
- **R2:** `test_no_checks_file_is_no_checks`, `test_the_template_itself_is_unfilled`,
  `test_a_good_file_lists_each_check`, `test_checks_problem_<case>` (no sh block, two sh blocks,
  duplicate name, sh block above the first section, unreadable), `test_check_strict_reports_them`
- **R3:** `test_checks_lists_and_runs_nothing`, `test_checks_is_read_only_and_allowed`
- **R4:** `test_accept_passes_and_fails_by_exit_code`, `test_accept_times_out`,
  `test_accept_fails_a_check_that_dirties_the_tree`, `test_accept_runs_from_the_checkout_root`,
  `test_accept_with_no_file_passes`, `test_accept_is_never_allowed`
- **R5:** `test_ship_lists_then_runs_the_changes_checks_under_a_prompt`,
  `test_no_skill_lets_accept_run_unasked`, the existing every-command-has-a-rule and
  every-rule-is-used tests
- **R6:** `test_defaults.py` own-copy tests (word-for-word bullets), `test_nothing_local.py`
- **R7:** `sdlc.py accept 005` green
- **Gate:** `./check.sh`

## Rollback

`git revert` the change's commit restores everything, this repo's `.sdlc/setup.json` included. It
doesn't cover:
- **A host that added the `checks` allow rule** through a setup refresh: one inert line once the
  subcommand is gone, which the host deletes.
- **A change folder that holds a `checks.md`:** under the old code it's just an extra Markdown
  file, rendered into its issue and otherwise ignored.
- **Issue #5's body:** it stays as last synced.
