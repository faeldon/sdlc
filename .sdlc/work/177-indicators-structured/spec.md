---
id: 177
slug: indicators-structured
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 177 — The retrospective reads indicators as rows and shows them as a table · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code. Each one is a fact this design relies on:

- The architecture pass runs `retro.indicators` through `_evidence()` at `EVIDENCE_TIMEOUT` (60 s) and `EVIDENCE_LIMIT` (20,000 characters), and gives one row per command as `architecture.host` (`scripts/retro.py`, `_architecture()`). A failure is already a row with `exit` and `error`.
- The committed report is `retro_report()` → `render_report()` over `templates/retro.md`, written only by `cmd_retro_commit()` at `report_rel(day)` (`.sdlc/retros/<date>.md`) and printed by `sdlc.py retro --report`. It runs **no host command today**, and `test_retro.py` pins that ("the report runs none of the host's commands", about line 2169). This change has to move that rule: see *Contracts touched*.
- `TEMPLATE_READS["retro.md"]` lists what the script reads from a host's override (`Spend`, `{{spend}}`). `drift` reports an override that lacks one of them as `breaking`.
- `.sdlc/setup.json` records `templates/retro.md`'s hash, so editing the template means running `sdlc.py record` in the same change.
- Setup asks about `retro.evidence` only in `skills/setup/drafts.md` Step 2, and only when a product doc is being drafted. A setup that `readiness` calls `complete` reads `SKILL.md` alone and never reaches `drafts.md`.
- `scripts/indicators.py` is pure (no subprocess, no `sdlc.py`), so it is where the parsing goes.

The requirements:

1. **R1. The row shape.** An indicator's output counts as rows only when all of these hold:
   - every non-blank line of its stdout is one JSON object (JSON Lines);
   - each object has `name`, a non-empty string on one line of at most 200 characters;
   - each object has `value`, a finite JSON number that is not a boolean;
   - each object may have `unit`, a string on one line of at most 40 characters, or null, or no `unit` at all;
   - any other keys are kept in `retro`'s JSON as `extra` and never rendered;
   - a row is identified by `(name, unit)`, with a missing unit read as `""`.

   Test: `test_indicator_rows_are_read_from_json_lines` (in `tests/test_indicators.py`), which fails if a valid output isn't read as rows, or if `extra` is dropped or rendered.
2. **R2. Anything else passes through as it does today.** In any of these cases the command's row gets `rows: null`, `not_rows` with a short reason, and `output`, `exit`, `error` and `truncated` exactly as now:
   - one line that isn't such an object;
   - no non-blank line;
   - a `(name, unit)` that appears twice;
   - output cut at the limit;
   - a non-zero exit;
   - a timeout or an OSError.

   Tests: `test_the_hosts_indicators_run_without_a_product_doc` passes unchanged (plain `echo 7 cycles`), and `test_output_that_isnt_rows_passes_through_with_its_reason` checks each reason.
3. **R3. Parsed rows in `retro`'s JSON.** When the output is rows, the command's row holds:
   - `rows`: each one `{name, unit, value, last, change, extra}`, in the order the command printed them;
   - `not_rows: null`;
   - `output: null`, so the blob doesn't carry both copies.

   Test: `test_indicator_rows_reach_the_architecture_block`.
4. **R4. Against the last retrospective.**
   - `last` is the value of the same `(name, unit)` in the report committed by the newest `Retrospective` commit (`git show <sha>:<report_rel(date)>`), read back by `indicators.report_rows()`.
   - `last` is null when there is no earlier retrospective, no report at that commit, no row with that key, or the key appears more than once in that report.
   - `change` is `value − last`, rounded to 3 decimal places, and null whenever `last` is null.

   Test: `test_an_indicator_is_compared_with_the_last_retrospectives_report`, which fails if `last` is taken from anywhere but that commit's report, or is ever 0 in place of null.
5. **R5. The report shows them as a table.** `templates/retro.md` gains a `## Indicators` section holding `{{indicators}}`, after `## Spend`. For each command, in config order:
   - a line naming the command in a code span;
   - then either a table with the exact header `| Indicator | Unit | Value | Last retrospective | Change |`, its cells escaped (`|` as `\|`, a missing value as `—`, change signed as `+3` or `−2`);
   - or one sentence saying why there is no table: `failed: exited N`, `timed out`, or `output isn't indicator rows (<not_rows>), so it is in sdlc.py retro's output only`.

   The report never holds a command's raw output or stderr. Test: `test_the_report_renders_indicator_rows_as_a_table`, which fails if raw output or stderr appears in the report text.
6. **R6. An empty key says so.** With `retro.indicators` empty, `{{indicators}}` is `No indicators set: name commands in retro.indicators (.sdlc/config.toml) to see them here.` Test: `test_the_report_says_no_indicators_set`.
7. **R7. The report runs `retro.indicators` and nothing else.** `retro_report()` runs `retro.indicators` through `_evidence()`, under the same timeout and limit as the architecture pass. It never runs `retro.evidence` or `retro.test_times`. The existing assertion at `test_retro.py` about line 2169 becomes two:
   - an evidence or test-times command (`touch ran-evidence`) still leaves no file;
   - an indicator command does run.

   It fails if the report runs an evidence or test-times command.
8. **R8. Read back what was written.** `indicators.report_rows(render(...))` returns the same `(name, unit) → value` mapping the rendered table showed. This covers names holding `|`, integral and fractional floats, negative values and a missing unit. Test: `test_indicator_rows_round_trip_through_the_report`.
9. **R9. A host's override names the section.** `TEMPLATE_READS["retro.md"]` adds the heading `Indicators` and the placeholder `{{indicators}}`, so `sdlc._template_misses("retro.md", <override without it>)` names both. Test: extend the test at `test_retro.py` about line 2247.
10. **R10. `.sdlc/function-heat.py` prints the new shape.**
    - For each file's top `TOP` functions, ranked as today, it prints two rows:
      - `{"name": "<path>::<function>", "value": <commits>, "unit": "commits"}`;
      - the same name with `"value": <lines>, "unit": "lines"`.
    - It prints nothing for a file with no functions read.
    - It still prints function names and numbers only, and still exits 1 on a missing base branch.
    - For this repo's four files, its output stays under `EVIDENCE_LIMIT`.

    Tests: `tests/test_function_heat.py` updated to parse every line with `json.loads`, plus a check that its output is under the limit, since cutting at the limit would turn rows back into text.
11. **R11. Setup offers the key.**
    - `skills/setup/drafts.md` Step 2 gets an **Indicators** (`retro.indicators`) item. It is asked when `config`'s `retro.indicators` is empty, and it proposes commands that print figures only a language can tell (function heat, complexity, dependency cycles) as R1's rows. None is a fine answer.
    - Step 3's `.sdlc/config.toml` draft includes the key when one is given.
    - `retro.indicators` is added to `READS_CONFIG["sdlc:setup"]`.

    Test: `test_skills_read_host_specifics_from_config[sdlc:setup]` fails without the mention.
12. **R12. The docs say it, and setup's record matches.**
    - `docs/REFERENCE.md` *Retrospectives* documents R1–R7. It replaces "passed through as `host`".
    - *After an update* says an override of `retro.md` needs the `## Indicators` section.
    - `skills/retro/SKILL.md`'s `host` bullet describes `rows`, `last`, `change` and `not_rows`.
    - AGENTS.md's *Retrospectives* paragraph says the report runs `retro.indicators` as well.
    - `.sdlc/setup.json` is re-recorded with `sdlc.py record`.

    Test: `./check.sh`'s drift test fails while `sdlc.py drift` reports `templates/retro.md`.

## Design

**Parsing lives in `scripts/indicators.py`. It is pure, and gets two new functions:**

- `host_rows(output: str) -> tuple[list[dict] | None, str | None]` applies R1 and returns `(rows, None)` or `(None, reason)`. It uses `json.loads` per line, `math.isfinite`, and `type(v) is not bool`.
- `report_rows(text: str) -> dict[tuple[str, str], float | None]` finds every table in a report whose header line is exactly R5's header. It reads each body row by splitting on unescaped `|` and unescaping. A key seen twice maps to `None` (ambiguous), which R4 turns into `last: null`.

The cell escaping is one helper, `_cell()`, used by both the renderer and `report_rows`. R8 pins the round trip.

**`scripts/retro.py`:**

- **`_indicator_rows(home, trunk, ran: list[dict]) -> list[dict]`** takes `_evidence()`'s rows for `retro.indicators`. For each row it:
  - leaves `rows: None` with a reason when there is an `error` or `truncated` (`failed: exited N`, `timed out`, `truncated at 20000 characters`);
  - otherwise calls `indicators.host_rows(output)`.

  It reads the previous report once: `sdlc.last_retrospective(home, trunk)` → `sdlc._git(home, "show", f"{sha}:{report_rel(date)}")` → `indicators.report_rows()`. Then it fills `last` and `change`, and sets `output` to `None` where rows were read. A missing report, or no retrospective, gives an empty mapping and every `last` null.
- **`_architecture()`**'s `host` becomes `_indicator_rows(home, trunk, _evidence(home, cfg["retro"]["indicators"]))`.
- **`_indicators_text(host: list[dict], configured: bool) -> str`** renders R5 and R6. Tables use the existing `_table()` with its cells passed through `_cell()`. The `−` sign comes from the same formatter both ways, so the text the reader parses is what was written.
- **`render_report()`** gains `indicators: list[dict] | None = None`. With None (callers that pass nothing, the existing tests among them), `{{indicators}}` is R6's sentence. Its docstring says so.
- **`retro_report()`** runs the indicators once, through `_evidence()` → `_indicator_rows()`, and passes them in. Its docstring changes from "without … any host command" to "running only `retro.indicators`, as the architecture pass does".

**Edge cases:**

- **The run order in `retro-commit`.** It writes the report only after every refusal check passes, so an indicator runs only on a retro-commit that is going to commit. Its commit still names its paths explicitly (`-- *changed`). A command that writes a stray file therefore can't get it into the `Retrospective` commit, the same as `sdlc.py retro` today.
- **The two runs can differ.** `retro` in Step 0 and `retro-commit` in Step 6 each run the indicators. The report holds the second run. Between the two, `retro-commit` refuses any change in the tree, and `function-heat.py` reads the base branch, so for this repo the two agree. For a host, the committed figure is the one recorded. The skill's Step 0 JSON shows the first run, as it already does for every count.
- **A host's override of `retro.md` without `{{indicators}}`.** It renders without the section, as today, and `drift` flags it as `breaking` with the fix (R9). Its next retrospective then has no earlier table to compare against, and gets `last: null`.
- **A figure ranked out of the top `TOP`** has no row, and so no comparison. That is accepted: the debt index is about the top functions.

**`templates/retro.md`** gets `## Indicators` / `{{indicators}}` after `## Spend`. The note under the title loses "from the numbers `/sdlc:close` recorded" as the only source, and adds "and the host's `retro.indicators`". It stays one `>` note, inside `test_defaults.py`'s shape.

**`.sdlc/function-heat.py`:**

- `render()` becomes `rows()`, printing JSON Lines with `json.dumps(..., ensure_ascii=False)`.
- The "since …" header line goes, because the report's *Last retrospective* column says it.
- The module docstring is updated.
- `main()` stays as it is otherwise.

**Setup:** one item in `drafts.md` Step 2, beside **Evidence**, and the `.sdlc/config.toml` bullet in Step 3. `SKILL.md` is unchanged unless the open question below asks for more.

## Contracts touched

- **The report runs no host command (pinned by `test_retro.py` about line 2169, and by `retro_report()`'s docstring). This design changes it.** After this change the report runs `retro.indicators`, and only that. The reason: the intent asks for the figures *in the report*. The report is the only committed record a later retrospective can compare against, and `retro` can't hand its run to `retro-commit` without writing state outside the commit. `retro.evidence` (which can hold what users did) and `retro.test_times` (slow, megabytes) stay out, and R7 pins that. Your approval of this spec is the decision; with a no, the report can't carry the table, and R4–R9 go.
- **"`_evidence()`, the only place they run" (AGENTS.md, *Retrospectives*).** This still holds: the report runs them through `_evidence()`. The paragraph gets one clause saying the report runs `retro.indicators` too (R12).
- **`retro-commit` holds the direction doc, the register, the product doc and the report, nothing else.** Unchanged. No side file is added, because the comparison is read back from the report itself.
- **`metrics.py` and `indicators.py` are pure.** The new parsing in `indicators.py` uses only `json` and `math`. The git read stays in `retro.py`, through `sdlc._git`.
- **`breaking` is the script reading a new template heading, with `TEMPLATE_READS` getting the entry in the same change** (AGENTS.md, *Setup*). R9 does exactly that, and R12 re-records `.sdlc/setup.json` so the gate's drift check stays clean.
- **One shape for the shipped docs** (`tests/test_defaults.py`). The new section is a `##` with its placeholder inside it, and has no `---` lines.
- **Each skill names the config keys in `READS_CONFIG`.** R11 adds `retro.indicators` for setup. The retro skill's `host` bullet already names the key.
- **The scripts run on Windows.** There's no new subprocess. Lines are split with `splitlines()`. The report is still written with `newline="\n"`. `report_rel()` is already a POSIX string for `git show`.
- **Nothing about a project.** The test data uses neutral names (`src/drafts.py::save`, `cycles`).
- **The retro skill never quotes evidence into the direction doc, the product doc or the register.** Unchanged. The table goes only into the report, which the script writes.

## Alternatives rejected

- **A JSON array, or one object with a `rows` key, as the shape.** JSON Lines lets a shell indicator `printf` one row per line, needs no closing bracket to be valid, and still reads one line at a time. Allowing two forms would double what the reader and the docs have to explain.
- **`band`, thresholds, or a "better is lower" direction in the shape.** The plugin would then judge figures that are the host's to judge. `change` gives the trend, and a host can still add such a key, which is kept in `extra` for the retro skill to read.
- **Plain-text output rendered into the report.** It has no bound on content or shape, could leak paths or stderr into a committed file, and the intent asks only that it keep working. It stays in `retro`'s JSON, and the report says where to find it.
- **A side file (`.sdlc/retros/<date>.indicators.json`), or `Sdlc-Indicator:` trailers on the `Retrospective` commit, to hold the last figures.** A side file breaks "`retro-commit` commits these files and nothing else". Trailers would put about 120 lines into a commit message whose subject `last_retrospective()` matches. Reading back the table the script itself wrote needs neither.
- **`retro` caching its run for `retro-commit`.** `retro` writes nothing but stdout. A cache would be state outside any commit, and could go stale between Step 0 and Step 6.
- **Re-running each indicator at the last retrospective's commit.** That needs a checkout or worktree per run, doubles the cost, and assumes a command reads only the tree. `function-heat.py` reads the base branch, for one.
- **Comparing per command rather than per `(name, unit)` across the report.** Comparing per command would key on the command's text, so a renamed or re-quoted command would lose every comparison. A key that appears twice already gets no comparison, which is cheaper.
- **Raising `EVIDENCE_LIMIT` for indicators.** R10 keeps this repo's output well under it. A host whose output is cut gets `truncated` as its `not_rows`, which tells it what to fix.

## Verification

```bash
uv run --group dev pytest -q tests/test_indicators.py tests/test_retro.py tests/test_function_heat.py tests/test_skills.py tests/test_defaults.py
uv run --quiet --script .sdlc/function-heat.py | head -4
uv run --quiet --script scripts/sdlc.py retro | python3 -c 'import json,sys; h=json.load(sys.stdin)["architecture"]["host"]; print(h[0]["not_rows"], len(h[0]["rows"] or []), h[0]["output"])'
uv run --quiet --script scripts/sdlc.py retro --report | sed -n '/^## Indicators/,$p' | head -8
uv run --quiet --script scripts/sdlc.py drift
./check.sh
```

What healthy output looks like:

- **The tests:** all pass, including R1–R11's new tests and the R7-split assertion.
- **`function-heat.py | head -4`:** four lines like `{"name": "scripts/sdlc.py::main", "value": 13, "unit": "commits"}`, every one valid JSON.
- **`retro`:** `None 120 None` or near that (no reason, rows read, no raw output), from the main checkout's config, which names `function-heat.py`.
- **`retro --report`:** `## Indicators`, the line with the command in a code span, then R5's header. *Last retrospective* is `—` in every row until the first retrospective after this change.
- **`drift`:** nothing in `breaking` or `report` for `templates/retro.md`.
- **`./check.sh`:** green: ruff, format, pytest, and `claude plugin validate --strict`.

