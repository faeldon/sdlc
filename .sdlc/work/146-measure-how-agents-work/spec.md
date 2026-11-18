---
id: 146
slug: measure-how-agents-work
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 146 — Measure how factory agents work, not only how long · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Every count below is for one role in one change. It is read from the transcripts `measure` already
reads for that role: a factory agent's session (`runs/<role>.sessions`) and the sub-agents it
started, both through `metrics._run()`. A change built by hand gets an `Sdlc-Role` line only for
its sub-agents, as it does today. Tests live in `tests/test_metrics.py` unless another file is
named.

1. **R1. Each `Sdlc-Role:` line gains six named counts:** `edits=`, `shell_edits=`, `bg=`,
   `tool_errors=`, `test_runs=` and `broke=`. `test_a_role_s_behaviours_are_counted_from_its_transcript`
   builds a factory session fixture holding exactly one of each behaviour and finds each count at
   1 on the builder's `Sdlc-Role` line. It fails if any count is missing or comes out as 0 or 2.
2. **R2. `edits=` counts the role's `Edit`, `Write`, `MultiEdit` and `NotebookEdit` calls**
   (`EDIT_TOOLS`). `tool_errors=` counts the role's calls whose result has `is_error` true. A call
   with no result is no error, as on `Sdlc-Tool` today. Both are covered by R1's fixture, plus one
   interrupted call that adds nothing.
3. **R3. `shell_edits=` counts the role's `Bash` calls whose command writes a file**, by these
   shapes only:
   - a `>`, `>>` or `1>` redirect to a target that isn't under `/dev/` or a temp dir;
   - `tee`;
   - `sed -i` or `perl -i`;
   - `patch` or `git apply`;
   - an inline interpreter script (`python`/`python3`/`uv run python` with `-c` or a heredoc) that
     holds `write_text(`, `.write(` or `open(` with a `w` or `a` mode.

   `test_a_shell_edit_is_known_by_its_command` is parametrised over each shape (counted) and over
   `2>&1`, `> /dev/null`, `grep '>' f`, `sed -n` and a read-only `python -c` (not counted).
4. **R4. `bg=` counts the role's `Bash` calls that went to the background**:
   - its result's `toolUseResult` carries a string `backgroundTaskId`, which covers both
     `run_in_background: true` and the harness moving a command there after `timedOutAfterMs`;
   - or its command's last segment ends in a lone `&`.

   `test_a_backgrounded_command_is_known_by_its_result` has one fixture for each case, built from
   the shape recorded transcripts hold: `toolUseResult: {"stdout": "", …, "backgroundTaskId": "…",
   "timedOutAfterMs": 120000}`. It also has one `a && b` call that isn't counted.
5. **R5. `test_runs=` counts the role's `Bash` calls that run tests**:
   - the command starts with the host's `[commands] check`, or matches `HAND_GATE_RE`;
   - or any segment's program, looked up past `uv run [opts]`, `uvx`, `npx`, `python -m` and
     leading `VAR=` assignments, is in `TEST_RUNNERS` (`pytest`, `tox`, `nox`, `jest`, `vitest`,
     `mocha`, `rspec`, `go test`, `cargo test`, `npm|pnpm|yarn test`, `make test`).

   `test_a_test_run_is_known_by_its_program` counts `uv run --group dev pytest -q`, `./check.sh 2>&1
   | tail` (with `check = "./check.sh"`) and `python -m pytest`. It does not count `grep pytest x`
   or `cat pytest.ini`.
6. **R6. `broke=` counts a role's test runs that couldn't even parse or import the code right after
   it was edited.** Two things must both hold:
   - the run's output (the `tool_result` content, as a string or as text blocks) matches `BROKE_RE`:
     `SyntaxError`, `IndentationError`, `ImportError`, `ModuleNotFoundError`, `ERROR collecting`,
     `Cannot find module`, or `syntax error`;
   - the role made at least one edit or shell edit since its previous test run, or since its start.

   `test_a_broken_build_is_a_failed_parse_after_an_edit` counts that case once. It doesn't count the
   same output with no edit before it, or a failing assertion after an edit.
7. **R7. Each role's tools are listed by name and count on one new `Sdlc-Calls: <role>
   <name>=<n> …` line a role**, every name the role called, named by `_prompt_name()` as
   `Sdlc-Tool` names it, sorted by name. `test_a_role_s_tools_are_listed_by_name` finds
   `Bash:sed=2 Edit=1` for a fixture with those calls. It also finds that, for each name, the
   `Sdlc-Calls` counts summed over roles never exceed that name's `Sdlc-Tool` `calls=`.
8. **R8. Each factory role's `Sdlc-Role` line gains `model=`**: the model `runs/costs.jsonl`
   records for that role's sessions, matched by session id. Several distinct models are joined
   sorted with `,`. Each name goes through `_model_word()`, which turns anything outside
   `[A-Za-z0-9_.-]` into `-`, so a `:` never reaches `_value()`. With no `costs.jsonl` row for the
   session, `model=` is left off, never guessed. `test_a_role_s_model_comes_from_its_costs` covers
   one model, two models and none, and parses each line back with `parse_trailers()`.
9. **R9. Counted in the pass `measure` already makes.** The counts come from the entries `_run()`
   already loops over, and nothing reads a transcript a second time.
   `test_measuring_reads_each_transcript_once` wraps `metrics._lines` with a call counter, runs
   `measure_change()` over a factory fixture, and fails if any path is read twice.
10. **R10. A failure to count is never a stop.** An exception in counting one role's behaviours
    drops only that role's six counts, its `model=` and its `Sdlc-Calls` line. It adds `
    behaviour=failed` to `Sdlc-Coverage`, as `rework=failed` works today. Every other trailer is
    written as before. `test_a_behaviour_count_that_fails_drops_only_its_fields` forces the
    counter to raise and finds the `Sdlc-Totals`, `Sdlc-Stage` and `Sdlc-Tool` lines unchanged.
11. **R11. Numbers and names only.** `test_behaviour_trailers_carry_no_text` builds a fixture whose
    commands, paths and outputs hold marker strings. It checks that no `Sdlc-Role` or `Sdlc-Calls`
    line holds a marker, a `/`, a `~` or a space inside a value.
12. **R12. An old `Close` commit reads the same.** `parse_trailers()` on a body from before this
    change returns the same dict it did, with no `calls` key and no new role fields.
    `test_a_close_from_before_behaviours_parses_as_before` pins a literal body. In retro, a role line
    without `edits=` is unrecorded, never zero (R14).
13. **R13. Retro compares agents by role and by model.** `_agents()` in `scripts/retro.py` groups
    the window's recorded role lines by `(role, model)`. For each group it gives the changes, the
    runs, and the per-change median of each of the six counts. The report shows them as an "Agents
    by role and model" table appended to `{{spend}}`. `test_retro_compares_agents_by_model`
    (`tests/test_retro.py`) closes two changes whose builders ran on `model-a` and `model-b` with
    different counts. It finds both rows, with their medians, in `retro_report()`'s text and in
    `retro`'s JSON `spend.agents.groups`.
14. **R14. Unrecorded is counted, not guessed.** A role line without `edits=` is left out of every
    group, and `spend.agents.unrecorded` counts it. A role with no `model=` groups under `unknown`.
    `test_retro_leaves_agents_from_before_behaviours_out` closes one change before this format and
    one after, and finds one group of one change and `unrecorded: 1`.
15. **R15. Each change's own role counts are printed only with `--metrics`.** `cmd_retro()` drops
    `spend.agents.changes` without it, as it drops `spend.changes` today. Those per-change rows are
    in close order, so the counts before and after a prompt rule (`bg=` around 140) can be read off
    them. `test_retro_prints_a_change_s_agent_counts_only_with_metrics` checks both ways.
16. **R16. The contract is written down where the policy says it lives.** `scripts/metrics.py`'s
    docstring names:
    - the six counts, `model=` and `Sdlc-Calls`;
    - the extended `subagent` event;
    - the new `read_events(..., models=None)` keyword;
    - the rule that a line without the fields is unrecorded.

    `docs/REFERENCE.md`'s *Metrics* says the same for a host. No test checks this; it is the
    review's to check.

## Design

**Facts checked in the code**

- **Factory sessions are already read as roles.** `measure_change()` (`scripts/sdlc.py`) reads
  `runs/<role>.sessions` from the branch (`_agent_sessions()`) and passes `roles` to
  `metrics.read_events()`.
- **That loop is the one place to count.** `read_events()` hands a factory session's kept entries
  to `_run()`, and hands each sub-agent's transcript to `_subagent()` → `_run()`. `_run()` already
  loops once over each run's entries, turns each `tool_use` into a `tool` event tagged with `role`
  (`_call()`), and sets each call's `error` from its `tool_result` (`_answered()`).
- **Role calls are already counted, just not split by role.** `summarize()` folds every `tool`
  event into `by_tool` whatever its role. A role's calls are on `Sdlc-Tool` today but not split
  out.
- **The model is on record per session.** `factory.py agent` appends `{"session", "role", "model",
  …}` to `runs/costs.jsonl` for every run (`record_cost()`), and that file is committed on the
  branch (board.py reads it from history). Its `model` is the `--model` the factory actually passed,
  so it holds even while seed 2026-11-18-41 (models read from the worktree) is open.
- **The transcript shapes were read, not assumed.** A recorded factory session in this repo shows a
  backgrounded `Bash` call's result entry with `toolUseResult.backgroundTaskId`, plus
  `timedOutAfterMs` when the harness moved it there itself. Its `tool_result.content` is a string.
- **`_value()` can't take tool names.** It reads any value holding both `:` and `,` as a `k:v`
  dict and `int()`s each part. A tool list like `tools=Bash:git:status:3,Edit:1` would therefore
  make `parse_trailers()` raise for every reader. Tool names need a line where they are keys.
- **Retro's report already has a home for this.** It fills `templates/retro.md`'s placeholders,
  `{{spend}}` among them, through `render_report()`. A host's overridden template keeps
  `{{spend}}`, but would never hold a new placeholder.

**In `scripts/metrics.py`**

- **`_run()` grows the counting.** It takes `check_cmd` and the run's `model` (both `None`-able),
  and keeps a `behaviour` dict and a `calls` dict beside its `tokens`, all inside its existing loop:
  - An assistant `tool_use` adds to `calls[_prompt_name(...)]` and, through `_shell()`, may mark
    the call as a shell edit, a backgrounded `&` command, or a test run. An `EDIT_TOOLS` call adds
    to `edits`. Each pending test run remembers whether an edit came since the last one.
  - A user `tool_result`, the entry `_answered()` already reads, adds `tool_errors` when
    `is_error` is true. It adds `bg` when the entry's `toolUseResult` is a dict with a string
    `backgroundTaskId`. When the result answers a pending test run that had an edit before it and
    its text matches `BROKE_RE`, it adds `broke`.
  - The `subagent` event gains `model` (when known), `behaviour` (the six counts) and `calls`.
    That counting runs under a `try`. On an exception, the event carries `behaviour: None`, and
    `summarize()` turns that into the coverage note in R10.
- **One segment splitter.** `_shell(command, check)` is a pure helper that returns `(writes, bg,
  test)`. It shares the splitting with `_prompt_name()`: the splitter is pulled out as
  `_segments()`, and `_prompt_name()`'s output stays the same, which its existing tests pin.
  - Redirects are found after quoted spans and heredoc bodies are blanked.
  - The inline-script markers are searched only inside an interpreter's `-c` argument or heredoc
    body.
  - Temp-dir targets are `/tmp/`, `/private/tmp/`, `/var/folders/` and a `$TMPDIR` or `${TMPDIR}`
    prefix.

  Every count is a lower bound: a write by a shape not named, or a runner not in `TEMPLATE`
  `TEST_RUNNERS`, isn't counted. The docstring says so, as it already says stops are upper bounds.
- **`read_events()` gains `models: dict[str, str] | None = None`**, a session id → model map.
  Through `_run()` it puts `model` on a factory session's `subagent` event. A sub-agent's run gets
  no model: `costs.jsonl` has no row for it.
- **`summarize()` sums by role.** It adds each role's `behaviour` and `calls` to `roles[role]`,
  plus a sorted set of its models. When any of a role's runs had `behaviour: None`, the role keeps
  none of the new fields and coverage gains ` behaviour=failed`.
- **`trailers()` writes the new fields.** Each `Sdlc-Role` line gains `model=` (when any model is
  known) and the six counts, after its existing fields. A new `Sdlc-Calls: <role> <name>=<n> …`
  line follows the `Sdlc-Role` lines, one per role that called anything. The existing fields keep
  their order and meaning.
- **`parse_trailers()` reads the new line.** It reads `Sdlc-Calls` into `out["calls"][role]`. Role
  fields come through the existing `out["roles"][name]` path untouched: `model=` is a plain string
  because `_model_word()` leaves no `:`.

**In `scripts/sdlc.py`**

`measure_change()` reads `{folder}/runs/costs.jsonl` from the branch with `_git(main, "show", …)`
(nothing new is run), and parses each line as JSON, skipping what doesn't parse. It builds the
session → model map from the rows' `session` and `model` and passes it as `models`, beside
`roles`. A missing or unreadable file gives `{}`.

**In `scripts/retro.py`**

- **`_agents(changes)` builds the comparison.** For each change in the window it reads
  `metrics["roles"]`. It counts a role without `edits=` as `unrecorded`, and groups each recorded
  role by `(role, model or "unknown")`. Each group gets `changes`, summed `runs`, and the
  per-change median of each count. Per-change rows (`change`, `role`, `model`, the counts) go in
  `changes`, in close order.
- **`_spend()` returns it as `spend["agents"]`**, and `_spend_text()` appends an "Agents by role and
  model" table and the unrecorded count, after "Most errors".
- **`cmd_retro()` keeps one change's numbers out without `--metrics`.** It drops
  `spend.agents.changes` unless `--metrics` is given (`_lean()`'s rule).

**Edge cases**

- **A resumed session.** It is one session id with several `costs.jsonl` rows, all with the same
  model, so one name.
- **A restarted build.** It is a new session, possibly on another model, which gives
  `model=a,b`. Retro groups that as a group of its own, never split by guessing.
- **A role whose session has no kept entries.** It gets no `Sdlc-Role` line today, and gets
  nothing new.
- **A hand-built change.** It has no factory roles, so it gains nothing but its sub-agents' counts.

## Contracts touched

- **"The event list and trailer format are a contract: extend them, never redefine"**
  (*Metrics*). The design only adds:
  - fields at the end of `Sdlc-Role`;
  - a new `Sdlc-Calls` line;
  - new keys on the `subagent` event;
  - a keyword argument on `read_events()`.

  No existing field is renamed or changes meaning, and `Sdlc-Totals` and `Sdlc-Tool` are
  untouched. R12 pins an old body.
- **"Measuring never refuses."** R10: counting runs under its own `try`, and a failure only drops
  fields, as `rework=failed` works. Reading `costs.jsonl` is inside `measure_change()`'s existing
  `try`.
- **"`metrics.py` and `indicators.py` are pure: no subprocess and no import of `sdlc.py`."** All
  the new parsing is pure. `costs.jsonl` is read by `sdlc.py` and handed over as a dict.
- **"Numbers and names only: never a prompt, a reply, a path or a command"** (the intent's
  constraint and the module docstring). Commands and outputs are read inside `_run()` and only
  counts leave it. Tool names go through `_prompt_name()`/`_word()`, and models through
  `_model_word()`. R11 tests this.
- **Transcripts stay local.** They are read where they are and never copied. Test fixtures are
  built in `tmp_path` with neutral names (`model-a`, `reopen-drafts`), as `test_nothing_local`
  requires.
- **"A change's own numbers are printed only with `--metrics`."** R15.
- **Mechanism vs. policy.** `TEST_RUNNERS` names common runner programs, not anything a host
  builds, and the host's own `[commands] check` is read from the config `measure` already has. No
  new config key, so `READS_CONFIG`, `RETIRED_KEYS` and setup's drift are untouched.
- **Templates.** No template heading or placeholder is added (`TEMPLATE_READS` unchanged). The
  table rides in `{{spend}}`, so a host's overridden `retro.md` still shows it.
- **Windows.** No new subprocess or file write in the scripts. Retro's report write is unchanged.
- **REVIEW.md: "A transcript's shape assumed, not read."** The `bg` shape was read from a recorded
  transcript (see Design), and each fixture in R4–R6 is built from the shape of real entries. The
  `broke` test reads output from a `tool_result.content` string, the shape seen. The text-block
  list form is covered because `_entry_text()` already reads both.

No invariant needs to change.

## Alternatives rejected

- **Prose notes on an agent's habits.** The person ruled this out: it repeats every time and is a
  storage problem. A habit worth watching becomes a named count.
- **A second pass, or a separate reader over the transcripts.** It doubles the read cost on every
  close and can disagree with the first pass about what a role's entries are.
- **Role columns on `Sdlc-Tool` (`builder=12`).** Its extra keys are already stage names. Mixing two
  namespaces on one line breaks the day a role and a stage share a name, and no reader could tell
  them apart.
- **The tool list inside `Sdlc-Role` (`tools=Bash:sed:2,Edit:1`).** `_value()` would read it as a
  `k:v` dict and `int("sed:2")` would raise, so every reader of that commit would fail.
- **Only the top few tools.** A cut hides exactly the rare call that matters (one `Write` against
  28 shell edits). One line per role is short in practice, and a trailer has no length limit.
- **The model from each transcript entry's `message.model`.** It would cover sub-agents too, but
  `costs.jsonl` is what the factory chose and what the board's `by_model` cost is keyed by. Using
  it keeps retro's model groups and the cost figures in step, and the intent names it.
- **A `metrics.test_commands` config key.** That is a new key to set up, record and keep from
  drifting, before any host has shown a runner `TEST_RUNNERS` misses. Add it when one does.
- **`broke=` from a failing exit alone.** A failing assertion is a test doing its job. Only a run
  that can't parse or import what was just edited says the edit broke the build.
- **A new `{{agents}}` placeholder in `templates/retro.md`.** It is a new template read
  (`TEMPLATE_READS`, a breaking change for setup), and a host's overridden template would never
  show it.
- **Backfilling by amending `Close` commits.** That rewrites the base branch's history, which close
  and release must never do. See the open question on backfill for what's left.

## Verification

```bash
uv run --group dev pytest -q tests/test_metrics.py tests/test_retro.py   # the new tests and the old: all pass
uv run --group dev pytest -q -m portable                                 # still passes: nothing platform-bound added
./check.sh                                                               # ruff, format, the full suite, plugin validate: exit 0
```

What healthy looks like:

- In `tests/test_metrics.py`, every test named in R1–R12 passes, and so does every existing test,
  including `_prompt_name()`'s and `test_tool_lines_round_trip`. That is the proof the shared
  `_segments()` changed nothing.
- In `tests/test_retro.py`, R13–R15 pass, and so does
  `test_retro_compares_tool_prompts_only_where_close_recorded_them`.
- By hand, after the change lands: `git log -1 --format=%B <a factory change's Close commit>`
  shows, for example, `Sdlc-Role: builder runs=1 agent=… model=… edits=… shell_edits=… bg=…
  tool_errors=… test_runs=… broke=…` and an `Sdlc-Calls: builder …` line. `uv run --quiet --script
  scripts/sdlc.py retro --metrics` shows the builder's row under `spend.agents`.

**Boundaries**

- **Always:**
  - count only inside `_run()`'s one loop;
  - write only counts and names;
  - leave a field off rather than write a 0 nobody counted;
  - read old commits exactly as before.
- **Ask first:**
  - adding a behaviour beyond the six;
  - adding a config key;
  - any backfill of changes already closed (an open question below);
  - counting behaviours for the person's own session in a hand-built change.
- **Never:**
  - store prose about an agent's habits;
  - copy or commit a transcript;
  - run a subprocess from `metrics.py`;
  - rename or redefine an existing trailer field;
  - let a counting failure stop or slow a close.

