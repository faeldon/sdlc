---
id: 137
slug: approver-weighs-defaults
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 137 — The approver weighs the defaults it can, and the person decides the rest one at a time, with the alternatives in view · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions this spec rests on. Each was checked in the code, and the place is named:

- `decisions.md` is read line by line through one regex, `LEDGER_RE`. Its copies are `FACTORY_LEDGER_RE` in `scripts/sdlc.py` and `LEDGER_RE` in `scripts/board.py`. `tests/test_metrics.py` and `tests/test_board.py` pin both. Only a line that starts with `- [ ]` and doesn't match counts as garbled (`GARBLED_LEDGER`). So an indented line under a ledger line is invisible to every reader as they stand now.
- The approver's reply reaches the change only as `decision.md`, filed by `factory.py agent --task approve`. The supervisor's step 2 runs `decisions && verdicts` after every step, the approve step included. So `decisions` runs after the approver and before `stage test`.
- `read_ledger()` already has one ticked mark that is not the person's word: `→ superseded by D<m>` (`decided` false, `open` false). The settled mark copies that shape.
- `land_parts()` and `land_signals()` take a line as "assumed" when it is `not d["decided"] and d["kind"] == "default"`. That predicate also catches superseded and (after this change) settled lines. `verdicts` and `decisions` use `open` instead.
- `needs_of()`/`answered()` in `sdlc.py` count every matched ledger line in `ledger_lines`. If a ledger holds only ticked lines, an ESCALATE reads as answered.
- 136's folder isn't in this worktree, so this spec can't check what 136 says an escalation means. That stays open (see the questions).

R1. **An agent gives a default's alternatives in its reply, and `decisions` files them under the ledger line.** The `- DECISION: [default] …` line may be followed by indented lines: `- OPTION: <option> — <pros and cons>`, two to four of them, the first being the default; then one `- WHY: <why the default was chosen>`. The same holds for `[blocking]`. `raised_decisions()` collects the run of `OPTION`/`WHY` lines straight after a `DECISION` line. `cmd_decisions()` writes them under the new ledger line, indented two spaces (`  - OPTION: …`, `  - WHY: …`), in the reply's order. `test_a_defaults_alternatives_reach_the_ledger_under_its_line` (tests/test_factory.py) gives a builder report such a line and finds this exact block in `decisions.md`.

R2. **A ledger with alternatives reads as it did, everywhere.** `LEDGER_RE` and its two copies don't change. `read_ledger()` adds `options` (a list of `{"option", "notes"}`, the default first) and `why` (or None) to each record. A line with no sub-lines reads as `options: []`, `why: None`, and every other field as before. Tests:
- `test_a_ledger_without_alternatives_reads_as_before`: a ledger written before this change gives the same records it gives today, plus the two new empty fields.
- `test_a_ledger_with_alternatives_is_not_garbled`, in tests/test_sdlc.py and tests/test_board.py: `factory_reading()` and the board's reader give the same `pending`/`assumed` for a ledger with sub-lines as without, and no `GARBLED_LEDGER`.

R3. **Options are added to a bare line once, never twice.** Two sources can fill a ledger line that has no `OPTION` sub-lines: a later raise of the same text that carries options, or the approver's `ESCALATED` line for it that carries options (R5). The first one `decisions` reads gets filed under it. A line that already has options never gets more. A rerun of `decisions` changes nothing. `test_options_fill_a_bare_line_once`: run `decisions` twice and the file's bytes are the same after the second run.

R4. **The prompts teach the shape.** `agents/builder.md` and each reviewer prompt that raises defaults show the `- OPTION:` / `- WHY:` lines with an example: `reviewer-code`, `reviewer-security`, `reviewer-ui`, `reviewer-ux`, and `reviewer-test` and `reviewer-behaviour` for their blocking ones. Each says a default owes two to four options, its own first. `test_agents_give_a_defaults_alternatives` (tests/test_skills.py) finds `- OPTION:` and `- WHY:` in each.

R5. **The approver weighs each open default, one line each.** `agents/approver.md` and the `approve` task's prompt in `_task()` name every open default by id. They ask for exactly one of these per open default:
- `- SETTLED: D<n>: <reason, naming where the spec, the code or a round answers it>`
- `- ESCALATED: D<n>: <why only the person can decide>`, optionally followed by R1's indented `OPTION`/`WHY` lines.

ESCALATE is still required while any default is escalated. A default with no line counts as escalated. The approver may never settle a blocking line, or a default about scope, policy, cost, a destructive operation, a secret or a published interface. `test_the_approver_is_asked_to_weigh_each_open_default` checks that the approve prompt names each open id and both line shapes. `test_the_build_session_brings_the_persons_decisions_to_them` is updated: its `"still unticked"` assertion becomes one for the new wording.

R6. **`decisions` marks what the approver settled, and only through the script.** `cmd_decisions()` reads the current `decision.md`, never a `decision-<n>.md` archive. For each `- SETTLED: D<n>: <reason>` on an open default, it ticks that line in place: `- [x] D<n> (…, default): <text> → settled by the approver: <reason>`. The constant is `SETTLED = " → settled by the approver: "`, and the sub-lines are kept. A SETTLED naming a line that is blocking, ticked, superseded or missing marks nothing. It is reported in a new `unsettled` list with why, as `unmarked` is for supersedes. The JSON gains `settled` (the ids marked this run). `test_the_approver_settles_one_default_and_escalates_another` gives the approver's reply one of each and checks three things: the settled line's exact text, the escalated line still open with its options filed, and the reason shown in `decision.md` unchanged. `test_a_settle_that_cant_apply_marks_nothing` is parametrized over blocking, decided, superseded and unknown ids.

R7. **A settled line is neither open nor the person's.** `read_ledger()` gives a settled line `settled: <reason>`, `decided: False` and `open: False`. Tests:
- `verdicts`' and `decisions`' `assumed` leave it out.
- `agent --task decided --decision D<n>` refuses it, as it refuses a superseded id (`test_a_settled_default_is_not_the_persons_word`).
- `upgrade_answer()` never reads one.

R8. **The landing tells an approver's call from the person's.** In `land_parts()`, `assumed` becomes the open defaults only (`d["open"] and d["kind"] == "default"`). It gains `settled`, a list of `{"id", "text", "reason"}`. `land_shown()` lists them under their own heading, `Settled by the approver`, apart from `Assumed decisions to confirm`. `_dispose()` ticks only unticked defaults, as now, so it never touches a settled line. `test_the_landing_shows_settled_defaults_apart_and_never_confirms_them`: after a `--by person` landing, the settled line still reads `→ settled by the approver:` and not `→ decided:`. The new predicate also stops the landing listing a superseded line as assumed. `test_a_superseded_default_is_neither_assumed_nor_a_signal_nor_a_decision` gains that assertion.

R9. **A settled default is a landing signal** *(the draft's answer to an open question; see below)*. `land_signals()` adds `defaults settled by the approver: D2, D4` when any line is settled, so a batch holding one isn't `clear`. The existing `decisions still open or assumed` and `assumed decisions to confirm` signals keep firing for open lines only. `test_a_settled_default_keeps_the_batch_from_passing_itself`.

R10. **Status and the board never read an approver's call as the person's answer.** `sdlc.py` gets `FACTORY_SETTLED`, a copy of `SETTLED`, and `board.py` gets its own copy; both are pinned beside the `LEDGER_RE` pins. `factory_reading()` and the board's reader don't count a settled line in `ledger_lines`. So if an ESCALATE's ledger holds only settled lines, `needs_of()` gives `read the escalation`, and `answered()` is false. `test_an_escalation_with_only_settled_defaults_is_not_answered` (tests/test_sdlc.py) and the board's twin. `needs_of()`'s `confirm N defaults` counts only open defaults, as now.

R11. **`measure` counts the approver's calls on their own.** `_factory_files()` adds `defaults_settled` (ledger lines carrying `FACTORY_SETTLED`). `metrics.rework()` writes it into `Sdlc-Rework` beside `defaults` and `defaults_open`. Neither of those changes meaning: `defaults` still counts every default line, and `defaults_open` the unticked ones. `metrics.py`'s docstring names the new key. `test_a_settled_default_is_counted_apart` (tests/test_metrics.py) extends `SUPERSEDED_LEDGER` with a settled line and asserts `(blocking, defaults, defaults_open, defaults_settled)`. A change built by hand has no key at all, never a zero (`test_metrics.py`'s "absent, never a zero" test covers the new key).

R12. **Ship shows both.** `skills/ship/factory.md`, Step 0 and Step 4:
- A `→ settled by the approver:` line is neither decided nor assumed. It is shown as its own list with its reason, never as an open item and never as the person's word.
- Each open default is shown with its `OPTION`/`WHY` lines as the ledger holds them.

`test_ship_shows_settled_defaults_apart` (tests/test_skills.py) checks the text.

R13. **`factory.py ask NNN` lists what a person has to decide, and writes nothing.** It is new and read-only. It refuses a change not at `stage: test`: a run at `build` asks its own blocking decisions through the supervisor. It prints:
- `decision`
- `items`: every open line in id order, each with `id`, `kind`, `source`, `reply` (the path of the reply that raised it: `build/round-<N>.md` or `reviews/round-<N>/<role>.md`, from `source`), `question` (the line's text), `options` (default first; empty on an old ledger), `why`, and `escalated` (the approver's reason from `decision.md`, or None)
- `settled`: id, text, reason

`test_ask_lists_open_items_with_their_background_and_writes_nothing` compares every file's bytes in the folder before and after. `test_ask_refuses_a_change_not_at_test`.

R14. **`ask --answered D2,D3` says what the change needs next, from ids alone.** `next` is one of:
- `decide`, while any line is still open
- `rebuild`, when any answered line's answer isn't `KEPT`, so the build doesn't follow it. With `decision` ESCALATE, `/sdlc-factory:build NNN` restarts it; with READY, `/sdlc:ship NNN` from its worktree, since `restart` refuses a READY
- `ship` otherwise

`KEPT = "the assumed default, confirmed"` is the answer `decide` writes when the default is kept. An id that isn't a decided line is refused. `test_ask_says_rebuild_when_an_answer_overturns_a_default` and `test_ask_says_ship_when_every_default_is_kept`.

R15. **`/sdlc-factory:decide NNN` walks one change's open items one at a time.** It is a new `plugins/factory/skills/decide/SKILL.md`:
- Frontmatter: `name: decide`; a description over 80 characters saying when not to use it (a run still building, which the supervisor asks; more than one change); `disable-model-invocation: true`; `allowed-tools` holding `Read`, `Edit`, `AskUserQuestion` and exactly the `Bash(...)` rules for `factory.py config *` and `factory.py ask *`.
- Step 0 runs `config` and `ask`.
- Each item gets its own dialog, never two changes or two items in one. The dialog shows the change's `NNN-slug`, the background (read from `reply`, the spec and `escalated`), the default and why, and each alternative with its notes. The options are the default first, then at most three alternatives; any more are listed in the question's text. An old ledger line offers `keep the default` / `change it`.
- These dialogs collect answers and write nothing. The one WAIT then asks `Record <n> answers in NNN-slug's decisions.md as shown? (yes / change one / no)` in an `AskUserQuestion` dialog, with the shared WAIT wording.
- On yes, it `Edit`s each line to `- [x] … → decided: <answer>`: `KEPT` for the default, the option's text for an alternative, and the person's words for anything typed. Then it runs `ask --answered <ids>` and says `next` in the person's words.

Tests:
- `sdlc-factory:decide` is added to `GATED`, `test_skills_were_found` and `READS_CONFIG` (with no keys), so the frontmatter, the one WAIT, the dialog, the 2–4 answers, the rules and `uv run` tests all cover it.
- `test_decide_writes_answers_only_after_its_wait` checks that no `Edit` instruction comes before the WAIT.
- `test_decide_never_takes_words_on_a_command_line`.

R16. **The supervisor's `decide` step keeps working, unchanged in what it does.** `skills/build/SKILL.md`'s `decide` step and `agent --task decided` are untouched. The build skill's sentence "the approver escalates while any is unconfirmed" becomes R5's rule. Its Step 1 restart and Step 4 report name settled lines as the approver's calls, apart from those still assumed. Every existing test in tests/test_factory.py and tests/test_skills.py about the supervisor's decisions passes unedited, apart from R5's one assertion.

R17. **The docs tell the truth.**
- `plugins/factory/README.md`: its *Decisions that are yours* section, its skill list (`/sdlc-factory:decide NNN`) and its file table.
- `factory.py`'s docstring, which gains `ask` in its usage and its *Decisions* paragraph.
- `docs/REFERENCE.md`'s needs paragraph (settled lines aren't counted).
- `AGENTS.md`'s list of the factory's writing skills (it gains `decide`).

## Design

**The ledger keeps one line per decision, and gains indented sub-lines.** A line reads as before. What's under it is new:

```
- [ ] D2 (builder round 1, default): Page the drafts list at 50?
  - OPTION: 50 — one screen's worth; long lists need a second page
  - OPTION: 100 — fewer pages; a slower first paint
  - WHY: the spec's list view shows 50
- [x] D3 (code round 1, default): Log the draft id? → settled by the approver: spec R4 forbids logging ids
```

`OPTION_RE = r"^\s+- OPTION:\s*(.+?)\s+—\s+(.+?)\s*$"` and `WHY_RE = r"^\s+- WHY:\s*(.+?)\s*$"` read both the reply and the ledger. `read_ledger()` attaches each run of them to the ledger line above it. The pinned readers in `sdlc.py` and `board.py` don't read options at all: they need only `FACTORY_SETTLED`, to leave settled lines out of `ledger_lines`.

**Who writes what.**

| writer | writes | how |
|---|---|---|
| `factory.py decisions` | new lines and their sub-lines; `→ superseded by`; `→ settled by the approver:`; options filled into a bare line | the only code that writes the ledger's shape |
| the supervisor (`build`'s `decide` step) | `→ decided: <answer>` on a blocking line | `Edit`, unchanged |
| `/sdlc-factory:decide` | `→ decided: <answer>` on an open line, after its WAIT | `Edit`, the same mark |
| `factory.py land` (`_dispose`) | `→ decided: the assumed default, confirmed when landing` on unticked defaults | unchanged |

The approver writes nothing. Its `SETTLED`/`ESCALATED` lines sit in `decision.md`, which `agent` files, and `decisions` turns them into ledger marks on its next run, the one right after `approve`. `SETTLED_RE = r"^\s*- SETTLED:\s*(D\d+):\s*(.+?)\s*$"`, and `ESCALATED_RE` has the same shape. A rerun finds the line already ticked and does nothing.

**After a restart**, the archived `decision-<n>.md` is never read again, so its settlements stay as they were marked: ledger history, read by the next approver as an earlier approver's call. `approver.md` tells it to ESCALATE, naming the line, if the new build no longer follows one.

**`ask` and `decide`.** `ask` is mechanism: what's open, where it came from, and, given ids, what's next. `decide` is judgment: it reads the raising reply around its `DECISION` line, and the spec section it touches, to word the background. It asks one item per dialog and gathers the answers. Then it asks its one gate and writes. Ids go on the command line, words never do. Defaults and blocking lines are asked the same way. Settled lines are shown at the start as one list ("the approver settled these: …"), and none is asked. A person who wants to overturn one can still edit the ledger, or ship it by hand, where it is shown.

**Edge cases.**
- An old ledger (no sub-lines): R2 and R15's two-option dialog.
- A default with one option, or none: it is filed as given. `decisions` reports it in `bare`, and the approver is asked to give options for any bare default it escalates.
- More than four options: all are filed, and `decide` offers the first four (the default and three) as dialog options.
- The approver names an id twice: the first line wins, and the second goes into `unsettled` with why.
- `decision.md` is READY with an escalated default (the approver broke its rule): no new stop. The landing already flags open lines (R9's neighbours), ship shows them, and `ask` reports `decision` so R14 points at `/sdlc:ship`.

### Boundaries

- **Always:** keep a settled line's mark distinct from `→ decided:`; leave archived decisions unread; write the ledger's shape only in `decisions`.
- **Asks first:** `decide` writes nothing before its one WAIT's yes; the landing doesn't pass itself while a default is settled (R9, pending the person's answer).
- **Never:** the approver settles a blocking line or ticks anything itself; `decide` takes words on a command line, asks two changes or two items in one dialog, runs an agent, or answers for the person; no skill is named `resolve`; no feature beyond the intent: no board column, no new `needs_of` text, no change to how blocking decisions are asked mid-run.

## Contracts touched

- **Agents that judge have no Write** (AGENTS.md, *The factory*). The approver keeps `Read, Grep, Glob`. Its settlements are lines in its reply, which `agent` files and `decisions` reads. Nothing it says reaches the ledger except through the script.
- **`decisions` is the only writer of the ledger's shape** (intent). Every new mark and the sub-lines are written there. `decide`'s writes are the existing `→ decided:` mark, made by `Edit` exactly as the supervisor's step makes it, so its shape doesn't change.
- **`factory.py` never imports `sdlc.py`; each reads the other's files through copies of its parsing, pinned by tests.** `SETTLED` gets two copies, `FACTORY_SETTLED` in `sdlc.py` and `SETTLED` in `board.py`, pinned in tests/test_metrics.py and tests/test_board.py beside the `LEDGER_RE` pins. `LEDGER_RE` doesn't change.
- **Writing skills** (`tests/test_skills.py`). `decide` has one WAIT in `SKILL.md`, asked in an `AskUserQuestion` dialog with two to four answers, where only a chosen yes approves. Its `allowed-tools` lists a `Bash(...)` rule per command, written exactly as it runs: no plain `Bash`, no `if` or loop. Every call is `uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py …`, and it runs `factory.py config`. The per-item dialogs gather answers and write nothing, so they are not gates. The one WAIT approves the writes.
- **Free text never travels on a command line** (the factory's `R<n>` rule). `decide` writes answers by `Edit`; `ask --answered` takes ids.
- **The landing passes itself only when no change carries a risk signal, and never as the person's** (AGENTS.md). R9 makes a settled default a signal. If the person answers otherwise, an approver's call lands `by=auto`, which still never reads as the person's.
- **Only the current `decision.md` is ever a run's decision** (AGENTS.md). `decisions` reads settlements from it alone.
- **Metrics: extend the trailer, never redefine it** (AGENTS.md, *Metrics*). `defaults_settled` is a new key; `defaults` and `defaults_open` keep their meaning. `metrics.py` stays pure, and the count is made in `sdlc.py`'s `_factory_files()`.
- **The scripts run on Windows.** Every new `write_text` passes `encoding="utf-8", newline="\n"`, and paths in `ask`'s output use `as_posix()`.
- **Nothing about a project.** Test data uses `008-reopen-drafts` and neutral defaults (paging, logging an id). The intent's change numbers stay out of tests and code.
- **AGENTS.md itself.** Its list of the factory's writing skills gains `decide`. That is the map catching up, not a change of policy. **No invariant moves.**

## Alternatives rejected

- **A new box, `- [~]`, for a settled line.** None of the three pinned `LEDGER_RE`s match it, and the garbled check only looks at `- [ ]`. Status, the board and `measure` would silently drop the line. `[x]` with its own mark is what `superseded` already does, and every reader already passes over it.
- **Settling as `[x] … → decided: <the approver's reason>`.** The intent's first constraint forbids it: `measure`, ship and the landing would count it as the person's word.
- **The approver editing `decisions.md`.** It has no Write, and must not get it.
- **Options inline on the one line** (`Options: a; b. Recommend a`, as blocking lines do today). Splitting free text on `;` is a guess. The line grows past what the board and status show. And `AskUserQuestion` needs the options apart. Indented sub-lines are invisible to every existing reader.
- **Recommend only, leaving every default for the person, sorted.** The intent's Outcome asks for settling, and recommending alone leaves 129's case (every reviewer PASS, escalated only for unticked defaults) as it was.
- **A stop when a default comes without options.** Each stop costs a mend round. The approver filling in options for the ones it escalates gets the person the same view for less.
- **`decide` taking every change with open items in one run.** The Outcome names one change. The build skill's rule is never two changes' questions in one dialog, and one change at a time keeps `next` simple. `/sdlc:status` already lists which changes need deciding.
- **Folding the supervisor's mid-run `decide` step into the new skill.** Mid-run, a blocking answer resumes the builder (`agent --task decided`) inside a live run. `decide` runs after the run, at `test`, and starts no agent. They share the ledger mark, and `ask` reads the same records. Sharing more would tie a live run to a skill the person runs on their own.
- **`decide` at `stage: build`.** A live supervisor may be asking the same blocking line in its own session, and two `Edit`s would race. `ask` refuses it.
- **A skill named `resolve`.** That already means rebasing a conflict.

## Verification

```bash
./check.sh
uv run --group dev pytest -q -n auto tests/test_factory.py tests/test_skills.py tests/test_land.py tests/test_metrics.py tests/test_board.py tests/test_sdlc.py
uv run --group dev pytest -q -m portable
```

Healthy means:
- `./check.sh` ends with ruff clean, `ruff format --check` unchanged, every test passing and `claude plugin validate --strict` valid for both plugins.
- Each test R1–R15 names passes, `test_skills_were_found` lists `sdlc-factory:decide`, and the `FACTORY_*` pin test passes with `SETTLED` among its names.

End to end, by hand in a scratch repo with the factory enabled:
1. Write a builder report with a `[default]` line and three `OPTION` lines, and a `decision.md` of `DECISION: ESCALATE` with one `SETTLED` and one `ESCALATED`. Then run `factory.py decisions 008`. `decisions.md` holds one settled line and one open line with its options; the JSON shows `settled: ["D1"]` and `unsettled: []`.
2. `factory.py stage 008 test && factory.py ask 008` lists D2 alone, with `options`, `why`, `reply` and `escalated`, and D1 under `settled`. `git status` shows nothing new.
3. `sdlc.py status` shows `confirm 1 default`, not 2.
4. `/sdlc-factory:decide 008` asks D2 in one dialog, then its one WAIT. On yes with the default kept, D2 reads `→ decided: the assumed default, confirmed`, and `ask 008 --answered D2` says `next: ship`.

