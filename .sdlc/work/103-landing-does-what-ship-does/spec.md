---
id: 103
slug: landing-does-what-ship-does
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 103 — The factory's landing does what ship does · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. Nothing in the intent's list excludes a change any more.** `land-check` no longer puts a change in `excluded` because it has acceptance checks, skills' cases in scope, undone notes or assumed decisions. Each of these is now a signal, so a batch holding one is never `clear`. `test_a_change_with_acceptance_checks_or_undone_items_is_in_the_batch_behind_the_persons_yes` (it replaces `test_a_change_with_acceptance_checks_or_undone_items_is_shipped_by_hand`) fails if such a change lands in `excluded`, or if `clear` is true.
2. **R2. `land-check` shows what the yes approves.** Each change in the batch carries five parts. `checks` is each acceptance check's `name` and `command`, from `preflight`'s `checks`. `cases` is the scope plus the cap per change, from `preflight`'s `cases` and `sdlc.py`'s `CASE_CAP["change"]` ($5). `undone` is each unticked item with its proposed disposition: `seed` with a title, or `dropped` with a reason. `assumed` is each unticked `default` decision from `decisions.md`: its id and text. `recover` is the `How to recover:` lines the change's commit will carry. A part is empty when the change has none. `test_land_check_shows_each_changes_checks_cases_notes_decisions_and_recovery` fails if any part is missing or wrong.
3. **R3. The script words the batch's question.** `land-check` prints `question`. It adds a clause for checks and cases, for dispositions and confirmations, and for `How to recover:`, each only when some change in the batch has one. With skills' cases in scope it also names the batch's total cost ceiling (the cap times the number of changes with cases). The skill asks exactly that text and never words its own. `test_the_landing_question_names_only_what_the_batch_holds` fails if a clause shows up for a batch without the thing it names, or goes missing for a batch with it.
4. **R4. `factory.py accept <NNN>` runs the change's acceptance checks through `sdlc.py accept`, and only that way.** It runs `sdlc.py accept` through `_sdlc()` in the change's worktree. It writes the attempt to `build/land-accept.md` in the gate file's shape: first line `ACCEPT: PASS|FAIL`, then one `## Attempt <k>` section per run with `Build:`, per check name and exit, and the tail of its output through `_placeholders()`. It exits 1 on a failure. It never reads or runs `checks.md` itself. `test_factory_accept_records_sdlc_accepts_verdict` fails if the record is missing or the verdict differs from `accept`'s.
5. **R5. `factory.py cases <NNN>` runs the skills' cases through `sdlc.py run-cases <NNN>`, for one change.** A pass writes `Skill evals: ran, <passed> of <cases>` to the change's `findings.md` note. A `skipped` run writes `Skill evals: skipped, <why>`. Both use the line `sdlc.py`'s `CASES_RE` reads, and both create `findings.md` the way the landing already does for `FRESH_SKIPPED` when the file is missing. A failed case writes no note and exits 1. `test_factory_cases_writes_the_note_ship_reads_or_stops` stands in for `_sdlc` and fails if a pass or skip leaves no note `CASES_RE` matches, or if a failure writes one.
6. **R6. Neither command can run without a prompt.** No skill's `allowed-tools` grants `factory.py accept` or `factory.py cases`. Neither name holds `eval`. Neither appears in `check.sh` or CI. `test_no_skill_lets_accept_run_unasked` gains the two `factory.py` commands and fails if any rule matches them.
7. **R7. `land` itself enforces checks and cases, not only the skill, and refuses before writing anything.** It refuses a change with acceptance checks unless the latest attempt in `build/land-accept.md` is `PASS` on the build as it stands. It refuses a change with cases in scope unless `findings.md`'s note says `Skill evals:`. `test_land_refuses_a_change_whose_checks_or_cases_havent_run` fails if either is refused late, `intent.md` leaves `stage: test`, or anything is committed.
8. **R8. On `--by person`, `land` writes the dispositions and confirmations before `sdlc.py ship`, in the change's worktree:**
   - **A carried item:** a `## [<id>] [idea] <title>` entry is appended to the register (`config`'s `work.register`), with its id from one `sdlc.py next-entry --count <n>` call. The body says what is left and points at the change's `notes.md`. The item is ticked in place as `- [x] <text> → seed: <id>`.
   - **A dropped item:** ticked as `- [x] <text> → dropped: <reason>`.
   - **Each assumed decision:** ticked in `decisions.md` as `- [x] … → decided: the assumed default, confirmed when landing`.

   Every edit is by line. `--by auto` stays refused, because each of these is a signal. If ship refuses after the writes, a rerun writes no second seed and no second tick. `test_a_landing_carries_drops_and_confirms_once` fails if a rerun duplicates an entry or a tick, or if `sdlc.py`'s `inbox_entries()` can't read a seed back.
9. **R9. The commit carries ship's paragraphs.** `land_message()` puts a `Carried forward:` paragraph, a `Dropped:` paragraph and a `How to recover:` paragraph after the body and before `Refs #N` and `Sdlc-Landed:`. Each paragraph is left out when empty. The first two are read from `notes.md`'s `→ seed:` and `→ dropped:` ticks, which keeps a rerun's message the same. The message never carries `Sdlc-Findings`. `test_a_landed_commit_says_who_passed_its_gate_and_carries_no_review_count` is extended and fails if a paragraph is missing, misplaced or present when empty.
10. **R10. The approver proposes the dispositions and the recovery.**
    - The approver prompt lists the irreversible paths the diff touches. Those come from the base branch's `[review] irreversible`, through `factory.py`'s copy of `risk_paths()`.
    - `agents/approver.md` asks for one `- UNDONE: <item text> → seed: <title>` or `→ dropped: <reason>` line per unticked item, and one `- RECOVER: <path or group>: <the way back>` line per irreversible path.
    - An undone item with no matching line is carried as a seed titled by its own text. It is never dropped without a stated reason.
    - A change that touches an irreversible path and has no `- RECOVER:` line is still excluded: `decision.md proposes no How to recover for <path>: ship it by hand`.

    `test_the_approver_proposes_dispositions_and_recovery` fails if the prompt leaves out the paths, if the fallback drops an item, or if a change with no `RECOVER` lands.
11. **R11. After a rebase, the acceptance checks run again.** After a `rebased` or `conflict` state, `land-verdicts` says `next: accept` for a change with checks. It comes after a green landing gate and before any review, until `build/land-accept.md` has a `PASS` on `landed_build()`. A `FAIL` is `stop`. `test_a_rebased_change_runs_its_checks_again_before_its_review` fails if the order is different, or if a red check doesn't stop.
12. **R12. Every change landed this way is the person's.** It carries `Sdlc-Landed: by=person`. Covered by R7's and R13's tests.
13. **R13. End to end, through `factory.py` alone.** A batch of three ready changes lands without `/sdlc:ship`: one with `checks.md`, one with an undone note and one touching a path the scratch repo's `[review] irreversible` names. Each change's `Close` commit is on `main`. The register holds the carried seed. The irreversible change's commit holds `How to recover:`. `test_a_batch_with_checks_a_note_and_an_irreversible_path_lands_through_factory_alone` fails if any step needs `/sdlc:ship`. The skills' cases can't run in a scratch repo, because `_cases_report()` is `available: false` outside this plugin's repo, so R5 covers them with a stand-in.
14. **R14. The docs say what the landing now does.** `plugins/factory/skills/land/SKILL.md` (description, Steps 0–4, Out of scope) and `plugins/factory/README.md` drop "shipped by hand" for checks, cases and notes. `./check.sh` passes, `test_skills.py`'s WAIT, dialog and rule tests included.

## Design

### Taken as given (checked in the code)

- **The skill can't write files.** `/sdlc-factory:land`'s `allowed-tools` holds `Read`, `AskUserQuestion` and `factory.py` rules only: no `Write` or `Edit`. Every write in this design is `factory.py`'s.
- **`factory.py` never imports `sdlc.py`.** It runs the `sdlc.py` of its own version through `_sdlc()` (`sdlc_path()`). `accept`, `run-cases`, `next-entry`, `preflight` and `ship` are all reached that way, and none of them changes.
- **`sdlc.py ship` refuses a lot.** It refuses while `notes.md` has an unticked item (`open_items()`), and while a diff with cases in scope has no `Skill evals:` note (`cmd_ship`, `CASES_RE`). So dispositions and the cases note must exist before `ship`, which is the first thing `land` runs on a `stage: test` change. Changing that refusal is out of scope.
- **A factory change is uncommitted until `land` commits it** (no agent commits). Its rebase happens after that commit (`cmd_land`: ship, commit, `base`).
- **Rule matching won't grant the new commands.** The skill's rule `factory.py land *` matches `land <args>` only, never `land-…` or another name. `accept` and `cases` match no rule the skill lists.
- **Ship by hand confirms assumed decisions without ticking them.** Its yes confirms them (`skills/ship/factory.md`). The landing ticks them, because the intent asks for the confirmations written down.
- **Undecided blocking decisions are out of scope.** `verdicts` returns `decide` while a blocking decision is unanswered, so a READY change never carries one. If one did, it stays a signal, as today, and this change doesn't touch it.

### The pieces

**`land_signals()`** loses the three `excluded` reasons and gains these signals: `acceptance checks to run: <n>`, `skills' cases in scope: <n>`, `undone notes to dispose of: <n>` and `assumed decisions to confirm: <ids>`. The existing `decisions still open or assumed` signal is kept. Its one remaining exclusion is an irreversible path with no `- RECOVER:` line (R10).

**`land_parts(folder, worktree, pre)`** (new, pure apart from reads) builds R2's five parts:
- **`checks`** comes from `pre["checks"]["checks"]`.
- **`cases`** comes from `pre["cases"]["scope"]`, with the cap as a constant pinned to `sdlc.py`'s `CASE_CAP["change"]` by a test, as the other copies are.
- **`undone`** pairs `pre["undone"]["items"]` with `decision.md`'s `- UNDONE:` lines by exact item text (new `UNDONE_RE`), falling back to a seed.
- **`assumed`** comes from `read_ledger()`.
- **`recover`** comes from `decision.md`'s `- RECOVER:` lines (new `RECOVER_RE`).

`cmd_land_check` adds the parts to each entry and builds `question` with `land_question(batch, base)`. Its fullest form:

> `Land <n> changes in this order, <NNN-slug, NNN-slug>, each shipped with its approver's impact, its acceptance checks and skills' cases run as shown (at most $<total>), its undone notes carried or dropped and its assumed decisions confirmed as shown, with how to recover shown, committed, brought up to date with <base> (a conflict resolved by its builder and reviewed again) and closed, pushed as git.push says? (yes / leave one out / no)`

The answers stay `yes / leave one out / no`. To change a proposed disposition, the person leaves that change out and ships it with `/sdlc:ship`, as today.

**`cmd_accept(root, ident)`** (new, `factory.py accept <NNN>`):
- It runs `_sdlc(["accept", name], worktree)` and writes the attempt to `build/land-accept.md` (path helper `land_accept_path()`), with the same reader shape as `read_gate_file()`.
- `Build:` is `landed_build()` once the change has its commit. Before that, it is a digest of `_tree_hashes()` over the changed paths outside the change's folder plus `checks.md`. That keeps the record from changing the identity it records. The plan pins this hash.
- It emits `accept`'s JSON as it came, plus `verdict` and `to`.

**`cmd_cases(root, ident)`** (new, `factory.py cases <NNN>`):
- It runs `_sdlc(["run-cases", name], worktree)`.
- On exit 0 it writes the `Skill evals:` line into `findings.md`'s note: `ran, <passed> of <cases>` from the run's scores, or `skipped, <why>` from `skipped`. An existing `Skill evals:` line is replaced, never duplicated.
- On exit 1 it writes nothing and emits `failed` and the run's folder.

**`cmd_land(…, by="person")`** works in this order. Every refusal comes before the first write:
1. It checks that the latest accept attempt passed on the build as it stands (R7).
2. It checks that the cases note is there (R7).
3. It checks that each irreversible path has a `RECOVER` line (R10).
4. It writes the dispositions and confirmations (R8):
   - The seeds' ids come from one `next-entry --count` call.
   - The register path comes from `config`'s `work.register`. When the register is missing, it is created from `templates["inbox.md"]` as `config` resolves it.
   - The append is skipped for an item already ticked `→ seed:`, so a rerun is harmless.
5. It runs `_set_impact` and `ship`.
6. It commits with `land_message()` (R9).
7. It runs `base`. `ship` then stages the register, `notes.md` and `decisions.md` along with everything else.

**`cmd_land_verdicts`** gains `next: accept`, between `gate` and `review`, while the change has checks and no `PASS` on `landed_build()`. `--close` already amends the landing's record (`build/land-accept.md` included) into the commit.

**The approve task's prompt** (`_task`, `task == "approve"`) appends the irreversible paths, read from the base branch's config next to `_sensitive()`, and asks for the `RECOVER` and `UNDONE` lines. `agents/approver.md` gains them under *What you return*. `IMPACT_RE`'s neighbours hold the two new regexes.

**`skills/land/SKILL.md`**:
- **Step 0 and Step 1** describe the new parts and signals.
- **Step 1** shows, for each change: each check's name and command, the cases and cap, each disposition, each assumed decision, and the `How to recover:` lines.
- **Step 2** asks `land-check`'s `question` as printed.
- **Step 3** gains a step 0 for each change: with checks, run `factory.py accept <NNN>`; with cases, run `factory.py cases <NNN>`. Both are named in prose, not in a bash block, and have no rule, so the harness prompts. A failure, or a declined prompt, stops this change and every one after it. Then `land`, and `accept` again when `land-verdicts` says so.
- **Step 4** reports each check, the cases run, and each disposition and where it went.
- **Out of scope** drops "Running `accept` or the skills' cases".

### Edge cases

- **The person declines the harness's prompt on `accept` or `cases`.** The change stops and is reported for `/sdlc:ship`. Nothing has been written, because `land` refuses without the record.
- **Cases skipped (no `claude`, eval unavailable, cost ceiling).** This is not a stop, as in ship. The note says why.
- **Cases after a rebase.** They are not rerun, because each run is paid. The rebased change gets the landing gate, `accept` again and the behaviour check. Step 4 says the cases ran before the rebase. (Left open, below.)
- **A seed title colliding with an existing entry's.** Ids are unique, and a match by title alone is never used (`ref_matches()`), so a collision is harmless.

### Boundaries

- **Always:** the person's yes before any of these writes. `accept` and `run-cases` only through `sdlc.py`, under the harness's prompt, one change per run. `Sdlc-Landed: by=person` for any change with these signals.
- **Asks first:** a disposition the approver didn't propose is never invented beyond "carry it as a seed". Missing recovery is a refusal, not a guess.
- **Never:** run checks or cases from `land` itself or from an allowed rule. Edit `sdlc.py`'s `accept`, `run-cases`, `ship` or `next-entry`. Land a change with these signals `by=auto`. Write the register from anything but the change's own worktree, committed with the change.

## Contracts touched

- **A writing skill has exactly one WAIT.** It asks in a dialog with 2–4 answers, and only a chosen yes approves. The landing keeps one WAIT and the same three answers. What it approves grows to the dispositions, confirmations, recovery and the runs, which is why this is Tier 2. `test_every_wait_asks_in_a_dialog` and `test_every_gate_offers_two_to_four_answers` still cover it.
- **Acceptance checks run only through `accept`, never pre-approved.** `factory.py accept` is a pass-through to `sdlc.py accept`. It holds no parsing of `checks.md` and no rule anywhere. R6's test extends `test_no_skill_lets_accept_run_unasked` to it. No agent gains a way to run a check (`test_no_agent_but_the_builder_runs_checks` unchanged).
- **`run-cases` is never in `ALLOW_RULES`, `allowed-tools`, `check.sh` or CI, and no command name holds `eval`.** `factory.py cases` stays out of all four, and its name is `cases`. The cap is `run-cases`'s own, $5 per change-scoped run, and each change has its own run, so the cap holds per change.
- **Every script call is `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/<own script>`.** The factory skill calls only `factory.py`. `sdlc.py` is reached through `_sdlc()`, never from the skill.
- **`[review] irreversible` is matched by the script and read from the base branch.** `land_signals()` reads it from `preflight` (`_risk_report()`, base branch config). The approver prompt uses `factory.py`'s pinned copy of `risk_paths()` on the base branch's config, as `_sensitive()` does.
- **Mechanism vs judgment.** The approver (an agent that read everything) proposes the dispositions and recovery, and the person's yes approves them. `factory.py` only writes what was approved.
- **The register.** Its ids come from `next_entry_ids()` through `sdlc.py next-entry`. Seeds land in the change's own commit, exactly as `/sdlc:ship`'s Step 6 writes them. `inbox-commit` stays the only code that commits the register on its own. The entry heading `factory.py` writes is a copy of the register's shape, pinned by reading it back through `inbox_entries()` in R8's test.
- **Frontmatter and ledgers are edited by line, never through YAML.** This covers `notes.md`, `decisions.md` and `intent.md`'s `impact:` (`_set_impact`, unchanged).
- **Writes before a WAIT.** None are added. `accept` and `cases` run, and their records are written, only after the yes.
- **Windows.** Every new `write_text` passes `encoding="utf-8", newline="\n"`. Paths shown are `as_posix()`. Recorded output goes through `_placeholders()`.
- **The factory's gate passes itself only when no change carries a risk signal.** Each new thing is a signal, so `auto` can never land them.
- **No invariant needs to change.**

## Alternatives rejected

- **Running `accept` and `run-cases` inside `land`.** `land *` is an allowed rule, so the checks and the paid run would go without a prompt. That breaks both contracts.
- **The skill calling `sdlc.py accept` or `run-cases` directly.** A factory skill may call only its own `factory.py`, and the factory's installed copy has no `sdlc.py` under `${CLAUDE_PLUGIN_ROOT}`.
- **One `run-cases` over the batch's union of cases.**
  - `run-cases` takes one change and scopes from that change's diff.
  - A union needs a new `sdlc.py` mode, which the intent rules out.
  - It would put up to $5 behind several changes, against the per-change cap.
  - A failure couldn't be pinned to one change, so "stops that change and those after it" couldn't hold.
- **A second question for each change with checks or cases.** O3 asks for one question per batch. The commands are shown in it, and the harness's own prompts on `accept` and `cases` are the constraint's, not another gate.
- **Running the cases after the commit, on the rebased change, as hand ship does.** `sdlc.py ship` refuses a scoped diff without the `Skill evals:` note, and `land` runs `ship` before `base`. Moving the run would mean loosening that refusal.
- **The landing session composing dispositions and `How to recover:`.** It has no `Write`, and its judgment would be a second, unreviewed one. The approver already reads `notes.md`, the diff and `plan.md`.
- **Dropping an undone item when nobody proposed a disposition.** A dropped note is never read again. Carrying it as a seed loses nothing.
- **Pasting `plan.md`'s `## Rollback` as `How to recover:` when there's no `RECOVER` line.** Rollback is written before the build and may not match the paths actually touched. A refusal is honest. Only changes approved before this change lands lack the line.
- **New `sdlc.py` commands (`dispose`, `confirm`).** These would be cleaner for the register's copy-pinning, but the intent limits `sdlc.py` to being called as it is.

## Verification

```bash
uv run --group dev pytest tests/test_land.py -q -n auto        # R1–R5, R7–R13: all pass, the renamed exclusion test included
uv run --group dev pytest tests/test_skills.py -q -n auto      # R6, R14: no rule grants factory.py accept/cases; one WAIT, its dialog, 2–4 answers; every bash command has a rule
uv run --group dev pytest tests/test_land.py -q -k "irreversible or rebased or once"   # the new cases on their own
./check.sh                                                      # ruff, format, the full suite, claude plugin validate --strict: all green
```

A healthy run shows no skips in `test_land.py` other than `needs_uv` on a machine without `uv`, and `./check.sh` exits 0. `git grep -n "factory.py \(accept\|cases\)" plugins/factory/skills` shows the two names only in prose in `land/SKILL.md`, never in `allowed-tools` or a bash block. `git grep -n "shipped by hand\|ship those by hand" plugins/factory` returns nothing about checks, cases or notes.

