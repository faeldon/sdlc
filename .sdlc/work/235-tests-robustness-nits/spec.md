---
id: 235
slug: tests-robustness-nits
kind: spec
created: 2026-11-23
updated: 2026-11-23
---

# 235 — tests robustness nits · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Each of the 31 nits was checked against the code as it stands on this branch. 29 still apply and
are fixed below. Two are retired, each with the reason written down: 2026-11-21-20 is stale, and
2026-11-21-8 is `wontfix` because the case it names can't happen. Every one of the 31 goes into the
change's `entries.md` (a `Retire` line, with a `Reason` line for each of the two), so close takes it
out of the register. Each "test" below fails on the code as it is now, or with the fix undone.

Nits taken in: 2026-11-20-45, 2026-11-20-46, 2026-11-20-48, 2026-11-20-54, 2026-11-20-59,
  2026-11-20-62, 2026-11-21-5, 2026-11-21-6, 2026-11-21-8, 2026-11-21-10, 2026-11-21-11,
  2026-11-21-13, 2026-11-21-14, 2026-11-21-15, 2026-11-21-17, 2026-11-21-18, 2026-11-21-19,
  2026-11-21-20, 2026-11-21-27, 2026-11-21-30, 2026-11-21-31, 2026-11-21-39, 2026-11-21-40,
  2026-11-21-41, 2026-11-22-4, 2026-11-22-5, 2026-11-22-28, 2026-11-22-31, 2026-11-22-32,
  2026-11-22-33, 2026-11-22-34

**Robustness: code and skill text**

R1. (2026-11-20-46) `run_state.uncarried()` gives a reason of its own for an open default that
`decision.md` lists as `- SETTLED:` but that has no `- CONFIRM:` line and is still unticked in the
ledger. That happens when `decisions` was skipped or refused the settle. The reason names the
SETTLED line and says the default is still open, so READY can carry it only on a `- CONFIRM:` line.
The reason must no longer be the bare "no `- CONFIRM:` line". A default named on neither line keeps
"no `- CONFIRM:` line" word for word, so `tests/prompts/mend-confirm.txt` and
`test_a_second_uncarried_ready_is_a_rerun` are unchanged. The test is a new `settled` case in
`test_ready_with_an_uncarried_default_is_mended` (`tests/test_factory_decisions.py`). It writes
`- SETTLED: D1: …` into `decision.md` after `_carried()` has run `decisions`, so the tick never
happens. It asserts the problem names `D1` and `SETTLED`. On today's code it fails, because the
problem reads "no `- CONFIRM:` line".

R2. (2026-11-21-5) `closing.fix_trailers()` and `closing.origin_trailer()` catch only
`(OSError, ValueError)` instead of every `Exception`. `OSError` covers a git that can't be run past
what `sdlc._git()` already catches. `ValueError` covers `UnicodeDecodeError` from a non-UTF-8 blob
that `git show` prints. Each still returns `[]` for those, so a git or read failure never fails a
close. A coding error inside either (`TypeError`, `KeyError`, `AttributeError`) now propagates. The
test is a new test in `tests/test_archive.py`. It monkeypatches `sdlc._git`, which `closing.py`
reaches through its live binding. A stand-in raising `OSError` or `UnicodeDecodeError` gives `[]`
from both functions. One raising `TypeError` makes both raise (`pytest.raises`). The `TypeError`
half fails on today's code.

R3. (2026-11-21-8) Retired as `wontfix`, with this reason. Both plugins come from one marketplace,
named `sdlc` (`sdlc@sdlc`, `sdlc-factory@sdlc`; the steps `cmd_update` prints name it). So an sdlc
read from a folder means the factory is read from the same folder. `_stale()` skips every
`local_source` install anyway, so a factory row checked on its own would never be stale.
`update_line()` is unchanged. No test.

R4. (2026-11-21-18) `cmd_intake()` sets `from_host` only when the issue body's first line, leading
whitespace stripped, starts with `UPSTREAM_MARKER`. A body that holds the marker further down
(quoted in a comment, say) is not from a host. `docs/REFERENCE.md` already says "an issue that
opens with", so that text stays. The test extends `test_intake_flags_an_issue_from_a_host`
(`tests/test_archive.py`) with a third issue whose body carries the marker on its second line, and
asserts `from_host` is `False` for it. That fails today: `in` matches anywhere.

R5. (2026-11-21-20) Retired as `stale`, with this reason. `_SCP_RE` already takes a host with no dot
(`[\w-]+(?:\.[\w-]+)*`). Nit 2026-11-21-21 fixed that, and
`test_upstream_cut_places_a_path_after_a_colon_and_an_scp_remote` pins it with
`git@localhost:x/y`, which has the same shape as `user@alias:path`. No code change.

R6. (2026-11-21-30) `sdlc.py preflight NNN --preview` with any of `--context`, `--nits`, `--bugs`,
`--closing` or `--split` exits 1 and prints nothing on stdout. Its stderr names the flags given and
says only `--question` takes them. It no longer quietly ignores them. The check comes before
`cmd_ship_preview` runs, and `--preview` alone works as before. Ship's skill runs `--preview` with
no flags (`skills/ship/SKILL.md`), so nothing that runs today is refused. The test is a new test in
`tests/test_preflight.py`, shaped like the existing "only word ship's question" test: `--preview
--nits` gives 1, empty stdout and the refusal. On today's code it exits 0 with the preview.

R7. (2026-11-22-32) Step 1 of `plugins/factory/skills/autopilot/SKILL.md` tells the model to pass a
goal given in the person's own words single-quoted (`--goal '<goal>'`), with each `'` in it written
as `'\''`, so `$`, backticks and `"` in it stay literal. The same goes for Step 3's `--begin`, which
passes the same goal. The bash blocks, and so their `Bash(...)` rules, are unchanged. The test is a
new test in `tests/test_skills.py` that asserts the step's text says to single-quote the goal.

**Tests**

R8. (2026-11-20-45) The `mv` case of `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused`
(`tests/test_train.py`) moves a tracked file other than `.gitignore`, one the replayed commit
doesn't own, onto `notes.txt`, which it added. It asserts the refusal names the old path and not
`notes.txt`. That pins on its own that a staged rename's old path is named when only the new path
is owned, and the `edit` case no longer shares its stray.

R9. (2026-11-20-48) The `closes` case of `test_ready_with_an_uncarried_default_is_mended` sets the
line through `_closing(root, "[12]")`, and asserts `factory.intent_closes(folder) == "[12]"` before
it reads `verdicts`. If the fixture's frontmatter changes so that nothing is written, the case
fails instead of passing on the problem text alone. The bare `read_text()` with no encoding there
goes away.

R10. (2026-11-20-54) `unused_fixtures()` (`tests/test_suite_shape.py`) reads `posonlyargs`,
`args` and `kwonlyargs`. `test_the_check_finds_a_fixture_never_used` gains a
`def test_three(*, capsys): …` that never names `capsys`, and asserts it is found. That fails
today. `BUILT_IN` stays a hand-kept set: its comment says why (it holds only the fixtures asked for
to be used, never for a side effect, which a list derived from pytest would not keep apart).

R11. (2026-11-20-59, 2026-11-20-62) `test_two_writers_at_once_leave_whole_lines`
(`tests/test_records_ledger.py`) runs `factory.py`'s `_vouch` in one process and `sdlc.py`'s
`_vouch` in the other, at once, under the shared records lock. Each process loads its own script
by path. The count drops from 200 appends each to 50 each. It asserts 100 whole lines whose digests
are exactly the 100 written.

R12. (2026-11-21-6) `test_idea_and_bug_offer_an_origin_line` also asserts three things about each
skill's step 3. The `Origin:` line is offered only when the person's account says it was found in
another repo. One found here gets no line. Every `Origin:` value the skill writes, in an entry shape
or in prose, is `host` (a regex over `Origin: <word>` and `Origin: <…>`, whose first word is
`host`). A skill telling the person to write `self`, or any other word, in other terms fails.

R13. (2026-11-21-10, 2026-11-21-11, one finding raised in two rounds) The fake `claude` in
`tests/test_update.py` opens its log and rows files with `encoding="utf-8"`. A new portable test
asserts every `open(` in `FAKE_CLAUDE` names `encoding="utf-8"`.

R14. (2026-11-21-13) `_listed()` (`tests/test_retro_hosts.py`) also lists a path under the own
repo's `.claude/worktrees/`. `test_two_fixture_hosts_give_known_counts` asserts it is counted in
`own` (2, not 1) and that `listed` grows by one.

R15. (2026-11-21-14) A new test lists two real fixture hosts and excludes one with `!`. It asserts
`read` is 1, `excluded` is 1, and the window's counts are the other host's alone. That fails if an
excluded host is still read.

R16. (2026-11-21-15) `test_host_figures_never_move_this_repos_figures` also compares the report's
`## Indicators` block, from `retro_report()`, with the list and without it. The fixture has a
`retro.indicators` command configured, so the block holds rows and not the no-indicators sentence.

R17. (2026-11-21-17) `test_a_doc_drift_cannot_read_keeps_the_nudge`
(`tests/test_setup_lifecycle.py`) also uses a `drift` stand-in that raises `UnicodeDecodeError`,
and asserts the line stays. That pins the `ValueError` half of `setup_nudge()`'s
`except (OSError, ValueError)`.

R18. (2026-11-21-19) A new test in `tests/test_skills.py` asserts that the triage skill's entry
shape holds `Origin: <host, only for an issue intake flags `from_host`>`, and that its text says an
entry filed from such an issue carries `Origin: host`.

R19. (2026-11-21-27) `READ_ONLY_REFUSALS` (`tests/test_train.py`) gains a case where
`dereference-recurse` is grep's pattern and not `-d`'s value (`grep -n dereference-recurse
README.md`). It is refused, naming the word, and a comment says this is the trade-off D2 accepts.

R20. (2026-11-21-31) `test_every_wait_names_its_preview` matches each `PREVIEW_NAMES` word as a
whole word (`(?<![\w-])word(?![\w-])`), so `path` no longer matches `paths` or `xpath`. Where a
skill's text names the thing in another form, the list word changes to the form the text uses. The
skill text changes only if it really doesn't name the thing. A new portable test asserts the
matcher says `path` is absent from "the paths shown".

R21. (2026-11-21-39) A new portable test in `tests/test_hand_gate.py` asserts `factory.py`'s
`_hand_digests` and `_hand_hash` equal `sdlc.py`'s, compared as `ast.unparse` of each function with
its docstring dropped, as `tests/test_windows.py`'s `_function()` compares `_utf8_streams`.
`_hand_paths` and `hand_build` differ in a parameter name and in `COUNTER`, and stay pinned by
behaviour (`test_the_factorys_hand_build_is_sdlcs`).

R22. (2026-11-21-40) A new portable test in `tests/test_factory_ui.py` monkeypatches
`factory._binds` and `factory._only_time_wait` and asserts three cases. A refused bind with
TIME_WAIT alone is not lost. A refused bind with a listener is lost. A bind that succeeds is not
lost, whatever the table says.

R23. (2026-11-21-41) A new test in `tests/test_hand_gate.py` covers `_hand_digests()`'s sha256
fallback in both copies. A file whose path holds a newline gets the sha256 of its bytes. That half
is not portable: Windows has no such path. With `hash-object` made to fail (a `git` on PATH that
exits 1 for it, or `subprocess.run` patched to return a nonzero result), every present path gets
the sha256 of its bytes, and a deleted one stays `deleted`.

R24. (2026-11-22-4) A new test in `tests/test_base_ci.py` calls `base_ci()` with a home that is a
plain folder, not a repo. It gets `unknown` and asserts the folder is still empty afterwards. It
also calls `_write_ci_cache()` there and asserts nothing is written.

R25. (2026-11-22-5) A new test in `tests/test_base_ci.py` wraps `sdlc.os.replace` with a recorder
that calls the real one. After a `base_ci()` that caches, it asserts the cache was moved into place
from `sdlc-ci.json.<pid>.tmp`, that no `*.tmp` is left beside it, and that its bytes hold no `\r\n`.

R26. (2026-11-22-28) `tests/test_autopilot.py` builds `BUILDER_RAISES` from a module constant for
the recommended option (`keep it`). The end-to-end test asserts
`f"{factory.DECIDED_AUTOPILOT}{<that constant>}"` in the ledger and that `factory.DECIDED` is not in
it, so neither phrase is a literal far from what it depends on.

R27. (2026-11-22-31) `test_a_nit_no_later_round_raises_is_fixed_whatever_its_weights`
(`tests/test_factory_loop.py`) models its restart through `cmd_restart`, by `_restart()` after an
escalated run, as the R4 prompt tests near it do. It never sets `rounds[i]["start"]` by hand. It
asserts the nits of the round before the restart are `fixed` once the restart's first round is
complete and doesn't raise them.

R28. (2026-11-22-33) The bad cases of `test_the_planner_places_every_candidate` gain "empty WAVE
reason" and "empty LEAVE reason", each refused with "gives no reason".

R29. (2026-11-22-34) The same test gains a good case where a `- LEAVE:` line comes before any
`## <risk>` heading. `read_plan` accepts it, and the seed is in `plan["leave"]`.

R30. `./check.sh` passes, and every new test that names no POSIX-only behaviour is marked
`portable`.

## Design

**Assumptions checked in the code.**
- `sdlc._git()` catches `CalledProcessError` and `FileNotFoundError` and decodes as strict UTF-8,
  so what can still escape it is another `OSError` or a `UnicodeDecodeError`. `parse_entries()`,
  `frontmatter_list()` and `work_rel()` are pure. That is why R2's `(OSError, ValueError)` is
  enough.
- `closing.py` reaches `sdlc.py` through a live view (`sdlc.<name>`), so patching `sdlc._git`
  reaches it.
- `cli_preflight()` already refuses clause flags without `--question`. R6 extends that check to
  `--preview`.
- The marketplace name in the update steps is `UPDATE_MARKETPLACE` (`sdlc`), shared by both
  plugins, which settles R3.
- `landing.read_only_command()` refuses any word equal to `GREP_FOLLOWS_ACTION`, which is what R19
  pins.
- `retro._indicators_text()` writes the `## Indicators` block that R16 compares.

**Code.**
- `run_state.uncarried()` gets one more branch, placed before the "no `- CONFIRM:` line" fallback:
  `d["id"] in named and d["id"] not in confirms` gives the SETTLED reason. The other branches keep
  their order, so "named twice" still wins when an id has both lines. The text is built in the
  function, as the others are.
- In `closing.py`, the two `except Exception:` become `except (OSError, ValueError):`. Each
  docstring's "Never raises" becomes "never raises on a git or read failure". Nothing else in
  `closing.py` changes.
- In `cmd_intake()`, `from_host` becomes
  `(i.get("body") or "").lstrip().startswith(UPSTREAM_MARKER)`. The marker is the body's very
  first text when `upstream_send()` files it, so the first line and the opening are the same.
- In `cli_preflight()`, the `given` list is worked out before the `--preview` branch. With
  `--preview` and any flag given it prints
  `⚠  preflight: <flags> only word ship's question, which --preview doesn't ask; run --question for it.`
  and returns 1. The two-outputs refusal and the no-`--question` refusal stay as they are.
- In the autopilot skill, line 99's "quote a goal in their own words" becomes the single-quoting
  rule, and Step 3 says the same about `--goal`.

**Tests.** Each R names its file and what it asserts. New tests reuse the file's own helpers
(`_carried`, `_closing`, `_listed`, `_own`, `_retro`, `_restart`, `_reply`, `_run`, `_cfg`,
`_repo`), and no new helper module is needed. The ledger writer script in R11 takes the script's
path and the function's module as arguments, so one `WRITER` serves both copies.

**Boundaries.**
- *Always:* every nit in the list ends in `entries.md` as fixed or retired with its reason, and
  every edit keeps `encoding="utf-8"` and `newline="\n"`.
- *Ask first:* any change to a skill's bash block, a `Bash(...)` rule or a WAIT. None is planned.
  R20 may need a skill to name a preview's content in the form the list expects. If it does, the
  word in the list changes, not the WAIT.
- *Never:* a nit outside the list (2026-11-22-49's docs nits, 2026-11-22-51's style and refactor
  nits, even in the same files), a new feature, or any change to `update_line()`, `_SCP_RE`, the
  trailer format or what close commits.

## Contracts touched

- **`[review] sensitive`: `scripts/closing.py`.** R2 edits two `except` clauses there, so the
  change is held for the person, as the intent expects. The design stays inside "measuring never
  refuses": `fix_trailers()` and `origin_trailer()` are trailer builders, not `measure`, and a git
  or read failure still gives `[]`. Only a coding error, which a test should catch, now raises. That
  happens in `_step_remove_folder`, before the `Close` commit, and a rerun of close resumes from
  that step. `measure`'s own `except Exception` (line 514) is out of scope and unchanged.
- **Copies pinned across `sdlc.py` and `factory.py`.** R21 adds a body pin for `_hand_digests` and
  `_hand_hash`. Neither copy changes. `factory_records.py` is untouched.
- **The register: only through `entries.md` at close.** No edit to `.sdlc/work/inbox.md` on this
  branch. Every id is held in `entries.md`, and the `Nits taken in:` line above claims them, so
  `/sdlc:idea` can't retire one under the change.
- **Windows rules (`tests/test_windows.py`).** No new top-level platform import, every text write
  passes `newline="\n"`, and every text-mode `subprocess.run` in a test names `encoding="utf-8"`.
- **Skills (`tests/test_skills.py`).** The autopilot skill's text changes, but not its WAIT, bash
  blocks or `allowed-tools`. `test_only_autopilot_names_by_autopilot` is untouched.
- **Suite shape (`tests/test_suite_shape.py`).** After R10 the check also sees keyword-only
  fixtures. Every new test uses each fixture it asks for, and the widened check must still find
  nothing in the existing suite. If it finds one, that argument is dropped in this change.
- **Nothing local.** Test data stays neutral: no host name and no home path, the R14 worktree path
  included, which sits under `tmp_path`.

No invariant needs to change or be relaxed.

## Alternatives rejected

- **Fixing 2026-11-21-8 by checking the factory row when sdlc is read from a folder.** Both plugins
  share the `sdlc` marketplace, so that row is read from the same folder, and `_stale()` already
  skips it. The branch could never fire, and it would be code no test could reach honestly.
- **Saying in `--preview`'s help that it ignores the clause flags.** The command already refuses
  the same flags without `--question`. Refusing them here too keeps one rule ("only `--question`
  words with them"), and no caller passes them.
- **Catching `subprocess.SubprocessError` too in `closing.py`.** `_git()` already turns
  `CalledProcessError` into `None`, and the trailer builders run nothing else, so it would only
  hide a bug.
- **Deriving `BUILT_IN` from pytest's fixture list.** It would sweep in fixtures asked for their
  side effect (`recwarn`, `request`), which the check must not flag. The list is a judgment, and
  its comment says so.
- **Matching `UPSTREAM_MARKER` with its key and closing `-->`.** Intake has no key to match. The
  first-line rule is what REFERENCE.md and 209's R12 describe.
- **Splitting the tests nits and the robustness nits into two changes.** The seed asks for one
  change. Only R2 touches a sensitive path, and the change is held for the person once either way.

## Verification

```bash
uv run --group dev pytest -q -n auto tests/test_factory_decisions.py tests/test_archive.py \
  tests/test_preflight.py tests/test_skills.py tests/test_train.py tests/test_suite_shape.py \
  tests/test_records_ledger.py tests/test_update.py tests/test_retro_hosts.py \
  tests/test_setup_lifecycle.py tests/test_hand_gate.py tests/test_factory_ui.py \
  tests/test_base_ci.py tests/test_autopilot.py tests/test_factory_loop.py tests/test_prompts.py
uv run --group dev pytest -q -m portable
./check.sh
```

Healthy output:
- Every named file passes, and the portable run passes. That includes `test_windows.py`,
  `test_suite_shape.py`, and the new R13, R20, R21 and R22 tests.
- `./check.sh` ends green: ruff check, ruff format, the full suite, and
  `claude plugin validate --strict`.
- Undoing each code fix (R1, R2's narrowing, R4, R6, R10's `kwonlyargs`) makes its named test fail.
  The reviewer can check this by reverting one hunk.
- `tests/prompts/mend-confirm.txt` is unchanged.
- `entries.md` holds all 31 ids: 29 retired as fixed, 2026-11-21-20 as `stale` and 2026-11-21-8 as
  `wontfix`, each with its reason.

