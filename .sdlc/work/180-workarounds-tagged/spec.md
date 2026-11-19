---
id: 180
slug: workarounds-tagged
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 180 — Workarounds are recorded, so the retrospective counts them · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Nits taken in: 2026-11-19-26

**This change depends on 174** (`174-waste-tagged`). 174 adds `runs/ejections.jsonl` (`EJECTIONS`, in `factory.py` and copied into `factory_records.py`). `_record_ejection(folder, cause)` in `landing.py` writes it, from `_train_eject()` and `_train_stop()`, with one row per change put back: `{"at", "land", "cause": "gate"|"review"|"refusal"|"stop"}`. The row is written before `_amend_record()`, so it survives the `reset --keep`. This change reads that record and adds no override file of its own. It is built on 174 once 174 has landed, and the intent's `depends_on:` names 174.

Facts checked in the code before designing, so the requirements rest on them:

- Close fast-forwards (`_step_merge()`, `--ff-only`). So a change's own commits sit on the base branch's first-parent line, between where it started (`Sdlc-Base`, or `_change_base()`) and its `Close NNN-slug` commit (`closed_changes()`).
- The script writes only these commits on the base branch:
  - `Close <name>` (`_close_commit()`);
  - `Drop <name>` (`_drop_record()`);
  - the register's commits, whose subject joins `File …`, `Retire …`, `Update …` and `Triage …` parts with `; ` (`_inbox_commit()`, `INBOX_SUBJECTS`);
  - `Release <version>` (`cmd_release`);
  - `Retrospective YYYY-MM-DD` (`cmd_retro_commit`, `RETRO_RE`).
- Two skills commit by hand on the base branch:
  - setup: `Set the repo up for the sdlc plugin` and `Refresh the sdlc setup for <version>`;
  - uninstall: `Remove the sdlc plugin's setup`.
- An entry id is never handed out twice, including after it was deleted (`next_entry_ids()` reads every commit that ever added or removed one). So the register gaining an id it held before can only be a restoration.
- A fix the person asked for at landing leaves `build/land-<n>.ask.md` in the change's folder (`land_ask_path()`), and the change's commit keeps it.
- With no retrospective yet, `retro`'s window is all of history. Commits from before the repo took the plugin up (`_adoption_commit()`) are no workaround.

The requirements:

1. **R1. Each commit on the base branch is classed.** Every first-parent commit in the window, from the last retrospective (or the adoption commit) to the base branch's tip, is one of:
   - a closed change's own commit (in `<its base>..<its commit>`);
   - `Close`, `Drop`, a register commit (every `; ` part opens `File `, `Retire `, `Update ` or `Triage `), `Release X.Y.Z` or `Retrospective YYYY-MM-DD`;
   - one of setup's or uninstall's subjects;
   - **outside the loop**: anything else.

   Test (`tests/test_retro.py`): a fixture with one commit made by hand on the base branch between two closes counts exactly 1, and the same fixture without it counts 0. Each command's own commit there counts 0.
2. **R2. Code and records are told apart.** An outside commit that touches a record counts as `hand_record`; any other counts as `outside`. A record is a path under `CHANGE_FOLDERS`, `.sdlc/retros/`, `.sdlc/setup.json` or `.sdlc/last-id`. Each commit is listed with its short sha and subject. Test: a hand commit editing `.sdlc/work/inbox.md` counts as `hand_record`, and one editing a source file counts as `outside`.
3. **R3. A restored entry is counted.** Any first-parent commit in the window that adds to the register an id an earlier first-parent commit's register held counts as `restored`, listed by id and commit, whether an `inbox-commit` `File` or a `Close` filing a held entry made it. Test: a `Close` retires entry X, then `inbox-commit` files X again: `restored` is 1. Filing a new entry Y counts 0.
4. **R4. A stop's row names its train.** The row 174's `_record_ejection()` writes gains one field, `train`: the train's `began` from its state. Both callers pass it. 174's fields (`at`, `land`, `cause`) and their order are unchanged, and 174's reader ignores the new key. Test (`tests/test_train.py`): a stopped train of two committed changes leaves, in each change's commit, a `cause: stop` row with the same `train`. 174's `test_an_ejection_is_recorded_and_amended_in` still passes unchanged.
5. **R5. Recording never blocks.** A failure to append the row (`OSError`) is added to the eject's or stop's output as a `problems` entry, and the eject or stop goes ahead as it does today: the change is put back, the undo printed, and the train state written. Test: a stand-in for the append that raises `OSError` still leaves the change ejected, with its undo printed and a problem naming `runs/ejections.jsonl`. If 174 already lands this behaviour, the test pins it and the code is left as it is.
6. **R6. Retro reads the overrides.** It reads them from each closed and dropped change's own commit in the window, through `factory_records`:
   - `ejections(show)` gives `runs/ejections.jsonl`'s rows, with lines that don't parse passed over as 174's reader passes them over;
   - `land_asks(listing)` counts `build/land-<n>.ask.md`.

   The counts:
   - `ejections` counts the rows whose `cause` isn't `stop`, by cause;
   - `stops` counts distinct trains among the `stop` rows, by `train` (a row with no `train`, written before R4, counts once per change);
   - `fixes` counts the ask files.

   Test: two changes carrying the same train's `stop` row count `stops` as 1. One ejection by `gate` and one by `review` give `{"gate": 1, "review": 1}`. A `stop` row without `train` on each of two changes counts 2.
7. **R7. One block holds the counts.** `retro()`'s output gains `simplicity.workarounds`:
   - `outside`, `hand_record` and `restored`, each with its `count`, its `rows` and its `n` (the first-parent commits classed, or for `restored` the entries the register gained);
   - `overrides`, with `ejections`, `stops` and `fixes`, each with its `count` and `n`, the factory changes read. Each `count` is null, never 0, when `n` is 0.
   - `unknown`: a closed change whose start can't be found has only its own commit counted as its own. The commits before it are then unknown rather than outside, and a problem names the change.

   Test: a window with no factory change gives null overrides. A change with no base gives `unknown` and a problem, and no `outside` row for its commits.
8. **R8. Retro stays read-only.** The walk runs only git reads, and `retro` writes nothing new. The existing read-only tests still pass, and the new tests leave the fixture's `git status` and refs unchanged.
9. **R9. The review names the doc-claim class.** `.sdlc/REVIEW.md`, *The ways this repo's code fails*, gains the bullet **A doc's claim the change made false.**, in the idea's words, citing no change number. `tests/test_defaults.py` passes: the block sits under a heading the guide has, and restates none of it word for word.
10. **R10. The nit is answered.** `_lead_line()`'s docstring and `measure_change()`'s say that `errors` holds raw exception text for the person running close, and must never become a trailer. Test (`tests/test_metrics.py` or `tests/test_archive.py`): a stand-in `_lead_marks` raises `ValueError("<marker>")`. The marker is in `summary["errors"]` and in no trailer line `measure_change()` returns.
11. **R11. The copies are pinned.**
    - The ejection record is read under 174's names (`EJECTIONS`, in `RECORD_FILES`); this change adds no other name for it.
    - Core's reader of the ask files (`LAND_ASK_RE`, a core-only name) is pinned by a test that builds a path with `factory.land_ask_path()` and matches its name.
    - `ejections` and `land_asks` join `RECORD_NAMES`, so `tests/test_modules.py` keeps every record name in `factory_records.py`.
12. **R12. The docs say what is now true.**
    - `docs/REFERENCE.md`, *Retrospectives*, describes `simplicity.workarounds`.
    - `plugins/factory/README.md`'s line for `runs/ejections.jsonl` (174's) names the `train` field.
    - `skills/retro/SKILL.md`'s field list names `simplicity`.
    - `docs/RETRO-SCORECARD.md`'s *process overhead and workarounds* says what is now captured, and S6's row says it is done.

    This is the R9 class itself: the review checks it by grepping the docs for each name the diff touches.
13. **R13. The blind spot is named.** `UNMEASURED` gains `{"signal": "a change's own records edited by hand before it landed", "needs": "..."}`. A hand edit on a change's branch has no shape history can tell from a command's. Test: `retro()["unmeasured"]` holds it.

## Design

**Detection from history, in `scripts/retro.py`.** One new function, `_workarounds(home, cfg, since, changes, dropped, bases)`, called once by `retro()`, which puts its result under `simplicity`. It reuses what `retro()` already has: `changes`, `dropped` and `bases` (from `_change_rows()`).

1. **The span.**
   - `since["sha"]..trunk`, first-parent.
   - With no retrospective, `_adoption_commit()..trunk`.
   - With neither, the whole first-parent line, which then also holds the adoption commit (setup's subject).
   - One `git log --first-parent --format=%H%x00%h%x00%s --name-only` call gives every commit's subject and paths.
2. **Whose each commit is.**
   - For each closed change in the window, `git rev-list --first-parent <base>..<rec["sha"]>` names its own commits.
   - A change with no base claims only `rec["sha"]`. The commits after the commit before it on the line become `unknown`, and a problem names the change.
   - `Close` and `Drop` subjects are told by `CLOSE_PREFIX` and `DROP_PREFIX` with a `DIR_RE` name.
   - A register commit is told by splitting on `; `, against `INBOX_SUBJECTS` plus `Triage`.
   - A release is told by `^Release \d+\.\d+\.\d+$`, a retrospective by `RETRO_RE`.
   - Setup's and uninstall's subjects become constants, `SETUP_SUBJECTS`, in `sdlc.py` beside `CLOSE_PREFIX`. A test pins each one to the line in its `SKILL.md`, so a skill can't change its subject without the walk following.
3. **Outside or record.** For an outside commit, any changed path under `sdlc.CHANGE_FOLDERS`, `.sdlc/retros/`, `sdlc.MANIFEST` or `.sdlc/last-id` makes it `hand_record`; otherwise it is `outside`. Paths are compared as git prints them, POSIX on both sides.
4. **Restored entries.**
   - One `git log --first-parent -p --format=… -- <register>` over the whole line up to the window's tip, reading only entry heading lines (`ENTRY_RE`) added (`+`) or removed (`-`).
   - It builds, in order, the set of ids the register has ever held.
   - A window commit that adds an id already in that set is a restoration.
   - The register's path is built from `work_rel()` and `register_path()`, never a literal.
5. **Overrides.**
   - For each closed and dropped change in the window, `_records_at(home, rec)` gives `show` and `listing` at its own commit (a dropped one's tip).
   - `factory_records.ejections(show)` parses `runs/ejections.jsonl` with the same line parsing 174's `spend_rows()` uses for it. If 174 gives that parsing a function of its own, `ejections()` is that function and no second parser is written.
   - `factory_records.land_asks(listing)` counts `build/land-<n>.ask.md` by `LAND_ASK_RE`.
   - Only changes with a `decision.md` are in `n`, the same test `_autonomy()` uses (`autonomy_counts()` is not None).

**The ejection record, in `plugins/factory/scripts/landing.py` (174's, extended).**
- `_record_ejection(folder, cause, train)` takes the train's `began`. `_train_eject()` and `_train_stop()` pass `state["began"]`.
- The row is `{"at", "land", "cause", "train"}`: 174's three keys first, and `train` added last.
- The append is wrapped so an `OSError` comes back as a problem that each caller adds to its output (R5), rather than raising.

The record is still written where 174 writes it: after `_put_back()` and `_record_land()`, before `_amend_record()`. So the row rides into the change's commit, and the file's earlier rows come back with the folder's checkout, keeping every row through a re-land. No new file, constant or commit path is added.

**Edge cases.**
- A stop before any change was committed leaves no row and counts nothing. That is the stop's existing condition (`pre`), and the docs say so.
- A gate-fault ejection the loop makes itself counts under `cause: gate`, apart from `review` and `refusal`, so a reader can set it aside.
- A `stop` row written before R4 has no `train`, and counts once per change.
- A hand commit whose subject imitates a command's is counted as that command's. The count is a reading, not a guard, and REFERENCE.md says so.

**The nit, in `scripts/closing.py`.** These are docstring words only, in `_lead_line()` and `measure_change()`. The new test pins today's behaviour, so a later change that turns `errors` into a trailer fails it.

**The review bullet.** Added as the last bullet of `.sdlc/REVIEW.md`'s *The ways this repo's code fails*, in the idea's words: "**A doc's claim the change made false.** A sentence in `AGENTS.md`, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md` or a README that names the function, the command or the rule this diff changed, and still says what it did before. Grep the docs for each name the diff touches."

**Boundaries.**
- Always: rows are only appended, never rewritten. `retro` stays read-only. Every count carries its `n`, and a count with nothing to count over is null.
- Ask first: dropping or renaming any of 174's row fields; counting gate-fault ejections differently.
- Never: a new override file beside 174's; a trailer; a refusal because a workaround couldn't be recorded.

## Contracts touched

- **Retrospectives are read-only but for their report** (`retro()`; only `_evidence()` runs a host's command). The walk is `git log`, `rev-list` and `show` alone, runs no host command, and writes nothing. `retro-commit`'s set of files is unchanged.
- **Metrics' trailers are a contract, extended and never redefined.** No trailer is added or changed, and `scripts/metrics.py` is untouched.
- **A run's record format is extended, never redefined.** `train` is a new key on 174's row. 174's keys and their meaning stay, and 174's reader ignores an unknown key.
- **`[review] sensitive` names `closing.py` and `landing.py`.** Both are touched (a docstring, and one key and a caught error in `_record_ejection()`), so ship reviews the change at full depth with `sdlc:security`. Risk never changes the tier, which stays 2.
- **Core reads a factory run's files only through `factory_records.py`, with copies under `factory.py`'s names, pinned; `factory.py` never imports `sdlc.py`.** The ejection file is read under 174's `EJECTIONS`. `LAND_ASK_RE` is core's own name, pinned against `land_ask_path()`. No other core file names a record.
- **The landing commits only through `sdlc`'s `ship` and `close`; a branch moves only by `resolve --onto`, `land --close`, `--eject` and `--stop`.** No new commit or branch move: the row rides on the `_amend_record()` that eject and stop already run, after the landing's yes. No new write comes before a WAIT.
- **Recording a workaround never blocks it** (the intent's constraint). R5: a failed append is a problem in the output, never a refusal.
- **`.sdlc/REVIEW.md` holds only this repo's answers to the guide** (`tests/test_defaults.py`). The bullet sits under a heading the guide has, is this repo's own, and restates none of the guide. No `defaults/` or `guide/` file changes, so `sdlc.py record` isn't needed.
- **No literal work path; never `main` in a git call; ids by `names_change()`.** Paths come from `work_rel()`, `CHANGE_FOLDERS` and `register_path()`, the base from `cfg["git"]["base"]` as `trunk`, and ids by `ENTRY_RE`'s exact match.
- **The scripts run on Windows.** 174's append keeps `newline="\n"` and `encoding="utf-8"`. Paths compared with git's output are POSIX.
- **Nothing local.** Test data uses neutral ids and subjects. The review bullet cites no change number.
- **Skills' rules** (`tests/test_skills.py`). `skills/retro/SKILL.md` gains one field bullet and no command, so its `allowed-tools` don't change.

No invariant needs to change.

## Alternatives rejected

- **A file of this change's own (`runs/land-overrides.jsonl`), written beside 174's.** It would record the same ejections and stops twice, from the same two functions. Two records of one event drift apart, and the waste and workaround figures could then disagree about how many ejections there were.
- **Telling a stop's train apart by its rows' `at` times.** Each change's row is stamped as it is put back, seconds apart, and no window of seconds is safe. The train's `began` names it exactly.
- **A `Sdlc-Workaround` trailer on the `Close` commit.** The workarounds that matter most (a hand commit on the base, a restored entry) never pass through close. A new trailer would also widen the metrics contract for figures history already holds.
- **Asking the person to log a workaround.** The intent rules it out. A record that depends on someone remembering under pressure undercounts exactly when it matters.
- **Reading the train's state file.** It lives in the git common dir, never in history, and is removed when the train ends.
- **A workaround log committed on the base branch by the factory.** It would itself be a commit outside the loop, and the factory commits only through `ship` and `close`.
- **Matching commits on author or committer rather than subject.** Every commit, the plugin's included, is the repo owner's under git's configured user (AGENTS.md), so author tells nothing apart.
- **Detecting hand edits to a change's own records on its branch.** Nothing defines what a hand edit there looks like, against what the factory's commands write. It goes in `unmeasured` (R13) rather than being guessed at.
- **Putting the doc-claim bullet in `guide/review.md`.** The guide's *context* dimension already asks every repo whether its docs still tell the truth. Its failure-class slot is for "the failure classes its own history shows", and this bullet names this repo's docs from this repo's findings.
- **Rendering the counts in the committed report now.** The report's scorecard layout is S14's, later. A `{{…}}` placeholder now would make `templates/retro.md` a new template read (`TEMPLATE_READS`, a breaking change for a host's override).

## Verification

```bash
./check.sh
uv run --group dev pytest -q -n auto tests/test_retro.py tests/test_train.py tests/test_factory.py tests/test_modules.py tests/test_defaults.py tests/test_skills.py
uv run --group dev pytest -q -m portable
uv run --quiet --script scripts/sdlc.py retro
```

Healthy output:

- `./check.sh` ends green: ruff check and format clean, pytest all passed, `claude plugin validate --strict` ok.
- The named tests include the new ones for R1–R7, R10, R11 and R13, and 174's ejection test unchanged, all passing.
- The portable run passes.
- `sdlc.py retro`, in this repo, prints a `simplicity.workarounds` block:
  - `outside`, `hand_record` and `restored` each have an integer `count`, their `n` and their `rows`. Every row listed is a commit or entry a person can recognise as done by hand.
  - `overrides` has `ejections` by cause, `stops` and `fixes`, over `n` factory changes. Ejections and stops before 174 landed are absent, since no row recorded them.
  - `problems` names any change whose start couldn't be found.
  - `git status` in the main checkout is unchanged afterwards.

