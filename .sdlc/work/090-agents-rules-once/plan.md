---
id: 090
slug: agents-rules-once
kind: plan
created: 2026-11-17
updated: 2026-11-17
---

# 090 — Each rule is said once in AGENTS.md · plan

> Written by the builder after reading AGENTS.md's Architecture section against
> `docs/REFERENCE.md`, `docs/CONTRIBUTING.md`, `plugins/factory/README.md` and the docstrings and
> comments of every function and constant the section names.

## Files to change

- `AGENTS.md`: the Architecture section becomes a map. Each paragraph keeps its boundary and the
  rules no one function shows (the "never" rules a local edit would break), and points at the
  one place holding the detail. *Commands*, *Nothing public names the agent* and *Invariants the
  tests enforce* are unchanged.
- `scripts/sdlc.py`: docstrings and one comment that receive a rule AGENTS.md said alone (listed
  under *Moved* below); no code changes. (Planned: fix the module docstring's stale `work/` and
  point the map at it for the subcommands. Built: left alone, since it lists only half of them;
  the map doesn't point at it, and `notes.md` carries both.)
- `scripts/retro.py`: its module docstring receives the binding rules AGENTS.md said alone.
- `skills/ship/SKILL.md`: step 4's context pass gets a third question, whether the line is
  already said in another context doc or a docstring, and proposes a pointer rather than the
  line. (Built: the skill sat at its 475-line budget, `test_ship_s_skill_stays_under_its_budget`,
  so the second question and the bar's paragraph are reworded a line shorter each, saying the
  same, rather than raising the budget.)
- `docs/REFERENCE.md`: *The docs*' `docs.context` paragraph, which lists the pass's questions,
  gets the third, so it stays true.
- `docs/CONTRIBUTING.md`: its opening line said AGENTS.md has "the architecture function by
  function"; it now says it holds the map and points to where the detail lives.
- `.sdlc/work/090-agents-rules-once/checks.md` (new): acceptance checks.
- `factory.py` and `board.py` receive nothing: every rule cut from the board's and the factory's
  paragraphs is already said in their docstrings, their code comments or the factory's README.

## Where each cut rule lives

Every sentence of the old Architecture section, by paragraph: kept here, or where it is said.

| Old paragraph | Kept in AGENTS.md | Said elsewhere (verified) |
|---|---|---|
| Mechanism vs. judgment | all | — |
| Mechanism vs. policy | `load_config()` once; skills ask `config`; docs are answers | REFERENCE *The docs* (guide/defaults/templates, how answers are read, missing docs, the pre-1.5.0 copy, `reset`) |
| The base branch | all | — |
| Tiers and stages | all | — |
| `.sdlc/work/` committed | all but the move by hand, merged with `work_rel()` | REFERENCE *`.sdlc/work/` and worktrees* (move by hand, ignored folder refused) |
| `work_rel()` | the rule, the test, `HISTORY_WORK`'s readers | `work_rel()`, `checkout_of()` |
| Numbering | never fall back; the lock's place; `names_change()` | `ids_mode()`, `claim()`, `_main_lock()`, `next_id()`, `_worktree_highest()`, REFERENCE *Numbering*; Windows invariant (flock/msvcrt) |
| Trackers | by path; never reads `.sdlc/`; core never calls `gh`; `sync` never creates | `tracker()`, CONTRIBUTING *Writing a tracker*, REFERENCE *Trackers*, *The project doc* (one edit per field) |
| `cmd_base()` | the three writes before a WAIT; never a stash; never a merge of `main` | `cmd_base()`, `cmd_resolve()`, REFERENCE worktrees section; **moved**: `resolvable`, the factory's own resolve, the `refs/sdlc/*` state |
| Closing | refuses-on-loss; reruns; `push_failed`/`cleanup_failed`; cleanup from the base's config; never restores a deletion; handoffs named | `cmd_close()`, `_cleanup_plan()`, `_config_at()`, `_ff_deletions()`, `_push_plan()`, `_handoff()` and `HANDOFF_ENV`'s comment, `landing_reach()`, `_own_script()` and `OWN_SCRIPT_CMDS`' comment, CONTRIBUTING *When a change lands*, REFERENCE *Trackers* (`landed`, `Closes #N`); **moved**: the step order |
| Dropping | all, shortened | `cmd_drop()`, `_drop_record()` (`-s ours`, the counter), `dropped_changes()`, REFERENCE *Trackers* (not planned) |
| Releasing | `closed_changes()` the one walk; `_release_refusals()`'s danger; shims and `RETIRED_KEYS` | `unreleased()`, `cmd_release()`, `PREPARED_REF`'s comment, `cmd_publish()`, `_push()`, `_unpushed()`, REFERENCE *Releases* (boundary tag, `git tag -a`, `after_bump`, `prepare`, shims) |
| Retrospectives | read-only but its report; `retro-commit` alone writes the boundary; `_evidence()` keeps it out of `READ_ONLY`; rework is declared | `retro.py` module docstring, `_rework()`, `register_drift()`, `cmd_retro_commit()`, `retro_report()`, `process_views()`, `_architecture()`, `indicators.py`, `doc_items()`, REFERENCE *Retrospectives*, *The product doc*; **moved**: the default-argument rule, `sdlc.retro.<name>`, what stays in `sdlc.py` |
| The board | writes nothing; localhost; not allowed unasked; pinned copies; `textContent` | `board.py` module docstring, `_seen()`, `_progress()`, `typical_times()`, `_load_board()`, `board.html`'s comment, REFERENCE *The board* |
| The inbox | one register; seed vs idea; ids their own space; never by title alone; `inbox-commit` the only committer | `inbox_entries()`, `next_entry_ids()`, `ref_matches()`, `_seed_title()`, REFERENCE worktrees section (tags, `[seed]`, `ideas.md`, several `idea:` ids) |
| Bugs | folded into the register paragraph | `bug_entries()`, `severities()`, `cmd_inbox_commit()`, `_open_claims()`, `fix_trailers()`, `bugs_retro()`, `_review_at()`, REFERENCE (Bugs; retro proposes, never edits the review doc) |
| Intake | one record per issue, one reader; tracker only sets; record before telling | `recorded_issues()`, `mark_issues()` and its comment (`open_marks()`), REFERENCE (Issues people file); **moved**: the tracker only sets |
| Nits | `sdlc.py` only reads; the register test | `nit_entries()`, REFERENCE worktrees section (nits' lines and lifecycle) |
| Metrics | numbers only; the contract; never refuses; `_lean()` | `metrics.py` module docstring, `_lean()`, `_change_base()`, REFERENCE *Metrics* |
| Setup's record | three-way; `breaking`'s same-change rule; attribution has no default; nudge never a problem | `cmd_record()`, `drift()`, `_answers_drift()`, `attribution_status()`, `cmd_uninstall()`, REFERENCE *After an update*, `git.attribution` |
| Context docs | all | `cmd_context()` |
| Preflight | one call; the question is the script's; new part not new command; side files | `cmd_preflight()`, `ship_question()`, `SHIP_BRANCHES` |
| Setup's stop | `complete` errs toward false; the fixture test | `cmd_readiness()`, CONTRIBUTING *Layout* (`drafts.md`) |
| Review findings | the named exception; the script only reads; `fix` never commits | `findings_entries()`, `findings_trailer()`, `findings_fresh()`, REFERENCE (findings, the question) |
| Risk | script-matched, from the base branch; the reviewer's tools; never a tier | `risk_paths()`, `_risk_report()`, REFERENCE *Risky paths* |
| Acceptance checks | `accept` never pre-approved; never rerun later | `acceptance()`, REFERENCE (acceptance checks) |
| The skills' cases | this repo only; no `eval` name; never pre-approved or in the gate | `_cases_report()`, `cmd_run_cases()`, `cases_argv()`, `cases_nudge()`, CONTRIBUTING *The skills' cases* |
| The factory | the boundaries: never loaded by `sdlc`, never imports it, pinned copies, who edits, `agent`/`gate`/land as the one place for each, `Sdlc-Landed`, evidence, `checks.md`, `.sdlc/reports/` | factory README (*Where it sits*, *The agents*, *What it leaves*, *Mechanism*), `factory.py` module docstring, `model_for()`, `cmd_verdicts()`, `depth()`, `cmd_gate()`, `ui_review()`, `land_signals()`, `land_message()`, `UNSET_FOR_SDLC`, `sdlc_path()`, `change_root()`, `metrics.py` (`_supervised()`) |

### Moved (said nowhere else before this change)

- `cmd_base()`: `resolvable: true` when `resolve` can take the conflict on; the factory's landing
  resolves with its own `resolve`, so `base` never resolves itself.
- `cmd_resolve()` and the `RESOLVE_REFS` comment: refs, never a file in the tree, which the
  rebase would trip on (the four refs and their deletion with the branch were already in the
  comment); ship's side file is `skills/ship/conflict.md`.
- `cmd_close()`: the steps in order, a refused push as `push_failed`, and that close names the
  deletions in its question and never restores one. Its docstring's "the one write a skill makes
  before its WAIT" in `cmd_base()` was stale (there are three) and now says "one of the writes".
- `retro.py`: tests call its own names as `sdlc.retro.<name>`; a default argument can't read
  `sdlc`, unbound while it loads; what status and release call every run stays in `sdlc.py`.
- `recorded_issues()`: the tracker's `mark()`, `unmark()` and `needs_info()` only set what it
  decides, so a tracker still never reads `.sdlc/work/`.

## Work order

1. Docstrings: add each *Moved* rule to its function, so nothing is lost before the cut. Gate.
2. AGENTS.md: rewrite the Architecture section as the map, paragraph by paragraph against the
   table above. CONTRIBUTING.md's opening line. Gate.
3. Ship's context pass: the third question in `skills/ship/SKILL.md` and its mirror in
   REFERENCE.md. Gate.
4. `checks.md`: the acceptance checks below, each seen to fail on the old text.

## Tests

No suite test: this is prose, and only a deliberate revert could undo it. Acceptance checks in
`checks.md`:

- AGENTS.md is under 300 lines (it was 517; built: 293). Fails on the old text.
- Every function AGENTS.md names as `name()` is defined in `scripts/` or the factory's script, so
  a pointer never leads nowhere. Passes on the old text too: it guards the pointers rather than
  detecting a revert.
- Ship's context pass asks whether a line is already said elsewhere and proposes a pointer.
  Fails on the old text.

The existing gate covers the rest: `tests/test_skills.py` (ship's one WAIT, its rules),
`tests/test_nothing_local.py` (the rewritten text), ruff for the docstrings.

## Rollback

`git revert` undoes all of it: nothing is written outside the repo, and no data or published
artifact changes.
