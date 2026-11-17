VERDICT: PASS

## Notes

**Requirements checked**
- **R1–R3 (words, tool events, `Sdlc-Tool` lines):** each has code in `metrics.py` and a test, and none can pass without it.
  - `_words()` counts and no text leaves the reader.
  - `_call()` and `_answered()` give one event per `tool_use`, with `error` from the matching result's `is_error`. A call with no result stays `None`.
  - `trailers()` and `parse_trailers()` round-trip the tool lines.
  - A `Close` commit without `tools=` or `words=` is read as unrecorded, through `_unrecorded()`.
- **R4 (comment lines):** `comment_lines()` is pure and tracks the `+++` header so an added line that looks like one isn't misread. Prose is skipped and an unmarked suffix goes under `unknown_lines`.
- **R5–R8 (`spend` block):**
  - Medians need 3 changes (`SPEND_LEAST`), and an outlier is more than twice the median.
  - The tool ranking covers recorded changes only.
  - Missing counts stay `None`.
  - `why` is reported.
- **R9–R10 (template, skill, docs):** `## Spend` and its `TEMPLATE_READS` entry are in place, and the skill and REFERENCE.md describe the block.
- **R11:** correctly left for ship, as `notes.md` and the plan say.

**Decisions D1–D3:** I'm leaving all three as the builder's open defaults. Each one's reasoning is sound:
- D1: unrecorded changes are left out per measure, not from every median. This keeps the git-only comment view alive.
- D2: per-change rows print only with `--metrics`, as the contract requires.
- D3: added code lines come from the `-U0` diff.

**Contract checks**
- `indicators.py` and `metrics.py` stay pure, with no subprocess and no `sdlc` import.
- The one new git call goes through `sdlc._git`.
- The retro view stays read-only.
- Trailer keys are added, never redefined.

**Nits**
- `_words()` strips `<tag>…</tag>` spans from a typed reply to drop the harness's wrappers. A person's own pasted `<b>x</b>` is dropped from the count too. This is minor, and it undercounts rather than leaks text.
- `scripts/retro.py` `_spend_text`: the head says "N of the M changes closed recorded their tool calls and words". For a window where every change is unrecorded, the tier table's token medians still show. That is intended under D1, but a one-line pointer to it would help a reader.

**Done well:** one `-U0` diff serves both the code and the comment counts. The `# Windows` and `_kind()` reuse keeps tests and docs out of code lines. The unrecorded-versus-zero rule follows how `prompts=` already works.

**Ran:** `./check.sh` passes: ruff, format, pytest and both plugin validations. The only warning is the factory plugin's missing icon, which the validator says does not affect the result. I did not run `sdlc.py retro | jq .spend` against the main checkout's history.
