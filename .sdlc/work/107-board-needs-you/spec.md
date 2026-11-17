---
id: 107
slug: board-needs-you
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 107 — The board and status say what each change needs from you · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Facts this spec rests on, checked in the code. Line numbers are from this branch before 098 and 099
land. The plan rebases onto both first.

- The board puts a card in Needs you from `column()` (`scripts/board.py:608`). It does so for a file
  that won't read (any stage), for a stop or an unticked blocking decision (at `build`), and for
  `DECISION: ESCALATE` (at `test`). Nothing reads the ledger at `test`, so an escalation stays in
  Needs you after every line is ticked.
- `status` prints text (`print_status()`, `scripts/sdlc.py:8575`). It has no JSON output. What it
  prints comes from `analyze()`'s records, which the dispatch adds to (`sdlc.py:9153-9165`).
- The approver escalates for more than open decisions (`plugins/factory/agents/approver.md`, *How
  to decide*): an open Critical or High finding, a disagreement, a departure from the spec, a
  destructive operation. A run whose rounds ran out escalates with a `## Reconsider the approach`
  section (`factory.py`'s `RECONSIDER`). Ticking the ledger answers none of these.
- A spec is never on disk unapproved in either flow. `/sdlc:spec` and `/sdlc-factory:spec` write
  `spec.md` and stamp `stage: design` behind the same yes. So "approve its spec" can only be a
  Tier 2 at `plan` whose `spec.md` is filled while its stage never moved.
- In `decisions.md`, a ticked `R<k> (person, restart)` or `(person, revise)` line is not a ledger
  entry (`RESTART_WORDS_RE`, `REVISION_RE`). Every unticked line is a ledger entry.

1. **R1. One reader decides what a change needs.** `needs_of(rec)` is a new pure function in
   `scripts/sdlc.py`. It returns a list of short texts from the fields below, and reads nothing
   itself. The board calls it as `sdlc.needs_of`, and `status` calls it directly. Its tests drive
   it from a dict for each state below. `test_needs_of_reads_nothing` fails if it touches the file
   system or git.
2. **R2. A stopped run at `build` needs `stopped: <way>`** (`stopped: rerun`, `stopped: mend`,
   `stopped: ship`). A stop record that won't read needs `stopped: read runs/stopped.md`. At any
   other stage a stop record needs nothing. `test_a_stop_needs_its_way_on` fails otherwise.
3. **R3. An unticked blocking decision at `build` needs `decide D<n>`**, one per decision, in ledger
   order. `test_a_blocking_decision_needs_its_id` fails if the id is missing or the decision is
   listed at `test` without an ESCALATE.
4. **R4. An ESCALATE at `test` needs what its ledger and decision still hold:**
   - `decide D<n>` for each unticked blocking line;
   - `confirm N defaults` for N unticked default lines (`confirm 1 default` for one);
   - `reconsider the approach` when `decision.md` holds a `## Reconsider the approach` line;
   - `read the escalation` when the ledger holds no decision line at all (open question 3; this is
     the recommended answer).

   `test_an_escalation_needs_what_its_ledger_holds` covers each case and fails on a wrong or
   missing text.
5. **R5. An answered escalation is ready to ship.** An ESCALATE at `test` with at least one ledger
   line, every line ticked, and no Reconsider section has no needs. The board puts it in **Ready to
   ship**, with `answered: true` on the card and a badge reading `escalated: answered`.
   `test_an_answered_escalation_is_ready_to_ship` fails if it stays in Needs you, or if it moves
   without the badge.
6. **R6. An open box the ledger can't read is a problem, never an answer.** A `decisions.md` line
   opening `- [ ]` that `LEDGER_RE` doesn't match goes to `problems`, as
   `decisions.md: an open line that doesn't read as a decision`, and the card stays in Needs you.
   `test_a_malformed_open_line_keeps_the_escalation` fails if a garbled line lets an escalation
   count as answered.
7. **R7. A Tier 2 at `plan` with a filled `spec.md` needs `approve its spec`** (advance it to
   `stage: design`). A scaffolded `spec.md` needs nothing (the Plan column already says
   `/sdlc:spec`). `test_a_written_unapproved_spec_needs_approval` fails otherwise.
8. **R8. A file that won't read needs `fix: <the problem>`**, one per problem, at any stage. That
   is the board's existing `problems` lines, unchanged. The existing
   `test_a_file_that_wont_read_needs_the_person_at_any_stage` gains the assertion.
9. **R9. The column follows the needs.** `column()` puts a card in Needs you exactly when
   `needs_of` returns something. Problems still come before `close`, and `close` before a factory
   signal. The existing `test_each_factory_signal_counts_only_at_its_stage` keeps its expectations
   for 020–027, except 022: its ledger is empty, so under R4 it stays in Needs you, now needing
   `read the escalation`. A new case adds a ticked ledger and expects `ready`.
10. **R10. Each Needs you card names its needs.** The card shows a line `needs you: <a> · <b>` above
    `next:`, built with `textContent`. The flag `the approver escalated it to you` and the
    `<id> waits on you: <text>` flags stay, so the decision's words are still on the card.
    `test_a_needs_card_names_what_it_needs` reads the served page's script for the line and for
    `textContent`/`h()` use, and fails on `innerHTML`.
11. **R11. `status` ends with `■ What needs me`.** It is printed after `■ Problems`, one line per
    open change with needs (`    107  decide D2, confirm 3 defaults`), else `    nothing`. It
    replaces no line: the `stopped` mark and its `⚠`/`→` lines stay, since `/sdlc:status`'s
    precedence reads them. `test_status_ends_with_what_needs_me` fails if the section is missing,
    isn't last, or disagrees with the board's `needs` for the same folders.
12. **R12. `status`'s records gain keys and redefine none.** Each open record gains `needs` (a
    list) and `answered` (a bool). `decision`, `pending`, `assumed` and `reconsider` are read only
    for a folder holding `runs/`. Every existing key keeps its meaning. `test_status_records_only_gain_keys`
    compares the key sets before and after.
13. **R13. A poll rebuilds the board only when what's shown changes.** The render key is built from
    what the page displays: `touched_ago` as `ago()` renders it, `elapsed` as `dur()` renders it,
    `fraction` as the whole percent the bar draws. Raw seconds are never in the key.
    `test_the_render_key_holds_what_is_shown` reads the page's script and fails if `JSON.stringify`
    keys on raw `st.changes`.
14. **R14. Focus survives a rebuild.** When a rebuild does happen, the card that held focus
    (matched by `data-change`) gets it back, and an open drawer is untouched.
    `test_a_rebuild_puts_focus_back` fails if `render()` drops the `data-change` lookup and
    `.focus()` after `replaceChildren`.
15. **R15. `aria-live` is on the status line alone, and that line changes only when it has
    something to say.** `#board` loses `aria-live`. `#status` has `aria-live="polite"` and reads
    `live`, `live · N need you`, or the not-answering text. The poll time moves to a sibling
    `#polled` span with no `aria-live`. `test_aria_live_sits_on_the_status_line_alone` fails if any
    other node has it, or if `#status`'s text includes the time.
16. **R16. The docs say it.** `docs/REFERENCE.md`'s *The board* paragraph and its `status`
    paragraph describe the needs texts, the `escalated: answered` marker and `■ What needs me`.
    `skills/status/SKILL.md` names the section so the report doesn't re-derive it. The gate's
    `context` pass reviews them. No test.

## Design

**`needs_of(rec)` in `sdlc.py`.** This is the only place the rules live, so the board and status
can't disagree. It is pure. Its input is a dict holding `stage`, `tier`, `problems` (list of
str), `stopped` (`{"way", ...}` or None), `decision` (`READY`/`ESCALATE`/None), `reconsider`
(bool), `pending` and `assumed` (lists of `{"id", ...}`), `ledger_lines` (int) and `spec_filled`
(bool). It returns `list[str]`, and `answered(rec)` returns the R5 bool from the same fields. The
order:

1. Every problem (R8).
2. A closed stage (`shipped`, `dropped`) needs nothing more.
3. At `build`: the stop (R2), then the blocking decisions (R3).
4. At `test` with ESCALATE: R4's items, in the order listed there.
5. At `plan`, Tier 2, `spec_filled`: R7's item.

**Reading the files.**
- *The board* already reads `decision`, `pending` and `assumed` in `_factory()`. It gains:
  - `ledger_lines`, the count of `LEDGER_RE` matches;
  - the R6 check, which adds to `problems`;
  - `reconsider`, true when a line of `decision.md` stripped equals a new `RECONSIDER` copy;
  - `spec_filled`: `spec.md` in the artifacts and not in `unfilled`.

  `_entry()` sets `entry["needs"] = sdlc.needs_of(entry)` and `entry["answered"]` before
  `column()`.
- *`status`* reads the same fields in the dispatch loop (`sdlc.py:9156`), next to `factory_stop()`.
  It uses a new `factory_reading(folder)` that applies the existing `FACTORY_DECISION_RE` and
  `FACTORY_LEDGER_RE` and a new `FACTORY_RECONSIDER` to the folder on disk. `problems` for status
  is the record's `errors` plus R6's line. Status doesn't read `findings.md` or the gate record as
  the board does, so a problem only the board can see appears there alone. That is said in
  REFERENCE.md.

**`column()`** becomes, in order:
- `problems` → `needs-you`
- closed → `close`
- `needs` → `needs-you`
- `test` with ESCALATE (answered by then) or READY → `ready`
- else `seen` or `stage`

`next_action()` is unchanged: an answered escalation already gets `/sdlc:ship, or
/sdlc-factory:land with the others ready`. Landing still treats any ESCALATE as a risk signal
(`land_signals()`), so moving the card changes no gate.

**The page.**
- `card()` adds the `needs you:` line and the `escalated: answered` badge (as text, like the gate
  badge).
- `render()` builds its key with a `JSON.stringify` replacer that maps `touched_ago` → `ago(v)`,
  `elapsed` → `dur(v)` and `fraction` → `Math.round(v * 100)`.
- On a rebuild, `render()` records `document.activeElement?.dataset.change` first, then focuses
  `[data-change="…"]` (via `CSS.escape`, as `closeDrawer()` does) after `replaceChildren`, unless
  the drawer is open.
- `poll()` writes the time to `#polled`. `#status` gets new text only when its words change, so
  polite announcements fire when the board connects or drops, or when the count of cards in Needs
  you changes.
- The `Needs you` column's `who` reads `what each card says it needs`.

**Edge cases.**
- A ledger with only `R<k>` restart lines has zero ledger lines, so R4 gives `read the escalation`.
- `confirm 1 default` is singular.
- An escalation sent back (`decision-<n>.md`, stage `build`) reads only the current `decision.md`,
  as today.
- A change at `test` with no `decision.md` needs nothing, as 027 pins.

## Contracts touched

- **The board writes nothing, serves `127.0.0.1` alone, and builds every node with `textContent`.**
  New text goes through `h()`. No route, method or write is added. `test_the_board_writes_nothing`
  and `test_the_page_is_self_contained_and_never_parses_data_as_html` still pass unchanged.
- **The board loads only when `board` runs and calls shared code as `sdlc.<name>`.** `needs_of`
  lives in `sdlc.py`, and `status` never loads `board.py` (`test_status_never_loads_the_board`
  unchanged).
- **The board never stamps a stage, and moves a card by what the files say.** Needs are read from
  `decision.md`, `decisions.md`, `runs/stopped.md` and `spec.md` on every request, never written.
  The intent's constraint "answered only from its ledger" is kept: the ledger is necessary.
  R4's Reconsider and empty-ledger rules only narrow when it's enough.
- **Copies of `factory.py`'s parsing are pinned by tests.** The new `RECONSIDER` in `board.py` is
  added to `test_the_factory_parsing_is_a_pinned_copy`. `FACTORY_RECONSIDER` in `sdlc.py` is added
  to the pin in `tests/test_metrics.py` beside the other `FACTORY_*` copies. `factory.py` is not
  edited.
- **Status's output gains, never redefines.** The intent calls this "`status`'s JSON". There is no
  status JSON, so the contract applies to `analyze()`'s records (R12) and to the printed sections:
  one new section, none reworded.
- **Bad input in a host repo is a problem, never a traceback** (REVIEW.md). `factory_reading()`
  catches `OSError` and reports it, as `factory_stop()` does.
- **Windows.** No new subprocess or write. Reads use `encoding="utf-8", errors="replace"`. The new
  tests are `portable`, except the one that serves the page if its fixture isn't.
- **No new `READS_CONFIG` key, skill command or `allowed-tools` rule.** `skills/status/SKILL.md`
  gets prose only.

No invariant needs to change.

## Alternatives rejected

- **A column of its own for answered escalations.** The outcome says Ready to ship, with a marker.
  An answered escalation is shipped the same way as a READY. A seventh column would split one
  action across two places.
- **Answered = every ledger line ticked, nothing else.** That is the literal constraint, but it
  would move a Critical-finding or rounds-ran-out escalation with an empty or fully ticked ledger
  into Ready to ship. That is the wrong answer to "what needs me?", made at a glance. Hence R4's
  Reconsider and empty-ledger rules.
- **Computing needs in the page's JavaScript.** That gives two rule sets (page and status) that
  drift. The server decides once and the page only shows it.
- **Stamping a `needs:` field or a stage when the person answers.** The board writes nothing, and
  the intent says needs are read, never stamped.
- **Fixing focus by never rebuilding: patching cards in place.** It's a larger rewrite of
  `render()` and its keyed diff. A key built from what's shown, plus restoring focus, covers the
  bug. A running factory card's `dur()` still ticks each second under a minute, and restoring focus
  covers that.
- **Leaving the poll time in an `aria-live` status line.** That would make a screen reader announce
  every 2 seconds, which is worse than the bug.
- **Importing `factory.py`'s `read_ledger()`.** The core never imports the factory. Pinned copies
  are the established pattern.

## Verification

- `uv run --group dev pytest -q tests/test_board.py tests/test_sdlc.py tests/test_metrics.py -n auto`:
  all pass, including R1–R15's new tests and the updated 022 expectation.
- `uv run --group dev pytest -q -m portable`: passes. The new board and status tests run on
  Windows.
- `./check.sh`: ruff, the format check, the full suite and `claude plugin validate --strict` are
  green.
- By hand, in a scratch repo with:
  - a factory folder at `test`: `DECISION: ESCALATE` and `- [x] D1 (…, blocking): … → decided: …`;
  - another the same, with a `- [ ] D2 (…, blocking)` line and two unticked defaults.

  Run `uv run --quiet --script scripts/sdlc.py status`. It ends with `■ What needs me`, listing
  only the second as `decide D2, confirm 2 defaults`. Run `sdlc.py board --port 0` and open the
  printed URL:
  - the first card is in Ready to ship, badged `escalated: answered`;
  - the second is in Needs you with `needs you: decide D2 · confirm 2 defaults`;
  - Tab onto a card, wait 10 seconds, and focus is still on it (Enter opens its drawer);
  - with VoiceOver on, nothing is announced between polls.
```

