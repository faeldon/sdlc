---
id: 164
slug: prompts-in-files
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 164 — The factory's agent prompts live in files, not code · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions checked in the code before designing:
- Every prompt `cmd_agent` sends comes from `_task()` (`factory.py` ~4481). `_task()` calls `_task_prompt()`, which hands the landing's tasks to `_land_task()`. The prompt text in them is f-strings in those two functions, plus pieces kept elsewhere in the module: `MEND`, `VERDICT_MEND`, `DECISION_MEND`, `VERIFY_MEND` and `RECHECK` (~3716–3740), `weigh_text()` (~1934), `check_line()` (~3985) and the sentence `_land_diff()` returns (~4413).
- `_land_task` lives in `factory.py`, not in `landing.py`. It only calls `landing.train_names()` and `landing.land_verdict()`. So `landing.py`, which is in this repo's `[review] sensitive` list, needs no edit.
- The returned strings that are *refusals* go to the skill and the person, never to an agent. Examples: "verdicts says …", "no landing round is under way", `_NO_FORK`.
- `RECONSIDER` is a heading the script parses. `board.py` and `sdlc.py` keep pinned copies of it (`tests/test_board.py`, `tests/test_metrics.py`). It is not prompt prose.
- The script needs Python ≥ 3.11, so `string.Template.get_identifiers()` and `is_valid()` are available.
- `FACTORY_ROOT` (`Path(__file__).resolve().parents[1]`) already locates the factory plugin. `landing.py` is loaded from the script's own folder.
- No prompt text today contains a literal `$`. The only `$` in the module are in regexes and comments.

R1. Every prompt text a factory agent is sent lives in a file under `plugins/factory/prompts/`, one file per task. The text that varies is named placeholders the script fills. After the change, `factory.py` holds no prompt prose: neither `_task_prompt`, `_land_task`, `check_line`, `weigh_text`, `_land_diff`, nor any module constant. `test_no_prompt_prose_in_the_script` fails if one of the moved sentences (a fixed list of distinctive phrases, e.g. "Address every KEPT line", "keeping what both sides meant", "it waits for a gate slot") is found in `factory.py`'s source.

R2. The prompt for every task and every conditional branch, on fixtures, is byte-identical to what the unchanged script produced. `test_every_prompt_matches_its_recorded_copy` renders each case in the table below and compares it with a copy in `tests/prompts/<case>.txt`. The copies are recorded from the pre-change script. Before comparing, each value that varies by run (the temp root, `FACTORY_SCRIPT`'s path, commit ids) is replaced by a fixed mark. The test fails on any difference. The cases cover:
- `spec`: plain, upgraded, `--revise`, `--recheck`
- `build`: first; restart with and without a reconsider section and with and without the person's words; upgraded
- `fix`
- `review`: plain; upgraded; reworked with and without a kept change; with handed nits
- `verify`
- `rework`: with and without handed nits
- `approve`: plain; upgraded; stuck; untestable; exhausted; open defaults with and without bare ones; irreversible paths touched
- `decided`: builder-sourced and other
- `mend`: approver, verifier, verdict, builder, behaviour
- `resolve`: plain, and with inbox entries gone
- `train-resolve`
- `land-fix`
- `land-review`: no conflict, resolved, a fix asked for
- `land-verify`
- `land-mend`: verifier, verdict, evidence

R3. The recorded copies are the old script's output, not the new one's. The golden test loads `factory.py` from `SDLC_FACTORY_UNDER_TEST` when that is set, else from the repo. Run against a copy of the base branch's `plugins/factory/scripts/`, the same test passes too (see Verification). If a copy had been recorded from the refactored code and differed from the old output, that run would fail.

R4. Every part of every prompt file is used. `test_every_prompt_part_is_rendered` fails if a `(file, part)` in `PROMPT_PARTS` appears in no R2 case, or if a file or part on disk is missing from `PROMPT_PARTS`.

R5. A prompt file whose parts or placeholders don't match what the script fills is refused before any session starts:
- a part missing or extra;
- a placeholder the script doesn't fill;
- a placeholder the script fills that the part doesn't name;
- a stray `$` (`Template.is_valid()` false).

`_task()` returns the refusal string, so `cmd_agent` prints it under `refusals` with exit 1, and `claude` is never run. `test_a_prompt_file_that_doesnt_match_is_refused` covers each of the four shapes with a doctored copy of the folder (via a `PROMPTS_DIR` monkeypatch). It asserts exit 1, a refusal naming the file and part, and no fake-`claude` call.

R6. The person's free text and agents' text reach the prompt verbatim, even when they hold `$`, `${round}`, `{x}` or backticks. This covers revise words, restart words, a land-fix ask, reviewers' changes, nits, ledger answers and conflicted file names. Filled values are never parsed as templates. `test_filled_text_is_never_read_as_a_placeholder` fails if a `$`/`{}` in a person's revise words is changed or raises.

R7. Prompt files are read with `encoding="utf-8"`, and their line endings are normalised. A file checked out with CRLF (Windows `autocrlf`) gives the same prompt as one with LF. `test_a_crlf_prompt_file_gives_the_same_prompt` is marked `portable` and fails if a `\r` reaches a prompt.

R8. The script reads prompts only from its own plugin folder (`FACTORY_ROOT / "prompts"`), never from a host's `.sdlc/` or the worktree. `test_prompts_are_read_from_the_plugin_alone` puts a `.sdlc/templates/prompts/build.md` (and a `prompts/build.md` at the worktree root) in a fixture host and asserts the build prompt is unchanged.

R9. No prompt file holds a machine path or a project name. They are covered by the existing `tests/test_nothing_local.py` scan. `test_prompt_files_hold_no_path` fails if a file contains `/Users/`, `/home/`, a drive letter or `FACTORY_SCRIPT`'s path. Paths are only filled in at run time.

R10. The existing wording tests in `tests/test_factory.py`, `tests/test_land.py` and `tests/test_train.py` pass. They are not edited, except where they name a constant this change removes. For example, `factory.RECHECK` in the recheck test becomes the rendered recheck prompt. The diff to those files is limited to such renames.

R11. `plugins/factory/README.md` says where the prompts live, that they are read only from the plugin, and how a placeholder is written. `test_the_factory_readme_names_the_prompts_folder` fails if `plugins/factory/prompts/` is missing from it.

## Design

**Files.** `plugins/factory/prompts/<name>.md`, one per task:
- `spec`, `build`, `fix`, `review`, `verify`, `rework`, `approve`, `decided`, `mend`, `resolve`, `train-resolve`, `land-fix`, `land-review`, `land-verify`;
- one shared file, `common.md`: the `head` ("Change folder: … Worktree: … "), `check` (the `check_line` sentence), `land-diff` (`_land_diff`'s sentence) and `weigh` / `weigh-bare` (`weigh_text`'s two sentences).

`land-mend` uses `mend.md`'s `verify`/`verdict`/`evidence` parts and `land-review.md`, as it does today. Restart and upgrade are parts of `build`, `spec`, `review` and `approve`, not tasks of their own.

Each file is laid out like the shipped docs, for readers: a `# <name>` title, a `>` note saying the script fills it and the text is sent verbatim, then one `## <part>` section per piece of text. Part names match `^## ([a-z][a-z0-9-]*)$`, so a line like `## Evidence` in prose is never read as a part. A part's text is the lines under its heading, with the blank lines around it dropped (`strip("\n")`, never spaces). Its newlines are the prompt's newlines, and lines are not wrapped. The title and note are never sent.

**Conditionals stay in the script.** A file holds no logic. The script decides which parts to use, as today's `if`s do, and joins them with the joiners it uses today (`" "`, `"\n"`, `"\n\n"`). A part never starts or ends with whitespace, so the join is always the script's own. Lists and joined texts are computed in Python and passed as one value each. Examples: `'; '.join(state['settled']) or 'none'`, the verifier's `asked` lines, the train's `listed` lines. Example for `approve`: parts `main` ("Decide."), `upgraded`, `stuck`, `untestable`, `next-step`, `exhausted`, `undone`, `irreversible`. The `if` ladder in `_task_prompt` stays as it is; each `prompt += f"…"` becomes `prompt += " " + part("approve", "stuck", round=…, before=…, stuck=…)`.

**Placeholders: `string.Template`** (`${round}`, `$$` for a literal `$`).
- Prompt prose quotes backticks, `<...>` and, as prompts grow, braces (`{key S high}` nit weights, JSON). Under `str.format` every one of those braces would need doubling.
- A `$` almost never appears in prose, and none does today.
- `get_identifiers()` and `is_valid()` give the validation in R5 without a parser of our own.
- `substitute()` never re-reads a filled value, which gives R6.

**Validation.** `PROMPT_PARTS: dict[str, dict[str, frozenset[str]]]` in `factory.py` declares, for each file, each part and the exact placeholders the script fills in it. `_prompt_file(name)` reads `PROMPTS_DIR / f"{name}.md"` (`read_text(encoding="utf-8")`, which normalises CRLF). It splits the parts and checks:
- the part names equal the declared ones;
- each part `is_valid()`;
- each part's `get_identifiers()` set equals the declared set.

On any mismatch it returns a refusal string ("prompts/approve.md, part stuck: names ${rounds}, which the script doesn't fill"). `part(name, key, **values)` asserts `values.keys()` equals the declared set, then calls `substitute`. `_task()` first validates `common.md` and the task's file (plus `mend.md`/`land-review.md` for `land-mend`). It returns the first refusal before any branch runs, so a broken file refuses the task even when the broken part isn't the one this run needs. Nothing is half-filled. Files are read on each `_task()` call and never cached, since each `agent` is its own process.

**What moves.**
- Into files: every f-string body in `_task_prompt` and `_land_task`, `check_line`'s sentence (its path and id stay computed), `weigh_text`'s sentences (its id logic stays), `_land_diff`'s sentence (its fork logic stays), and the five mend/recheck constants, whose names are removed.
- Stays: `RECONSIDER`, filled as `${reconsider}`, because it is parsed and pinned elsewhere.
- Stays in code, unchanged: every refusal string, `_NO_FORK` included.
- `_task()` keeps adding the `check` part for the builder, as `check_line()` did. `check_line()` stays as a function returning the filled `common.md` `check` part, since tests and `_land_task` call it.

**The recorded copies.** The plan's first step adds `tests/test_prompts.py` and records `tests/prompts/*.txt` while `factory.py` is still unchanged. It then refactors and leaves the recordings alone. The marks for varying values:
- the temp root → `<root>`;
- `FACTORY_SCRIPT` → `<factory-script>`;
- each commit id the fixture knows → `<sha:name>`.

These marks are applied to the rendered text, never to the files.

**Edge cases.**
- A missing prompt file or folder is a refusal (R5), not a traceback.
- An empty value is filled as empty, as an f-string would.
- `cmd_agent`'s screenshot suffix for UI reviewers stays in code (see open questions).

## Contracts touched

- **`factory.py agent` is the one place the factory runs `claude`.** Unchanged: the files are text `_task()` reads, and nothing executes them. No new subprocess.
- **`factory.py` never imports `sdlc.py`; no new dependency.** It uses only `string.Template` from the stdlib. The PEP 723 block and the `dev` group are untouched.
- **The scripts run on Windows.** Files are read with `encoding="utf-8"`, and text mode's universal newlines strip CRLF (R7, `portable`). Nothing is written by the script. The test's own fixture writes pass `newline="\n"`, except the deliberate CRLF copy, which is written in binary.
- **Nothing about a project or a workspace.** Prompt files hold no paths (R9). The recorded copies hold only marks, never a temp or home path, so `test_nothing_local.py` passes over `tests/prompts/`.
- **Agents that judge have no Write; only the builder and the resolver edit.** The tool grants are untouched (`AGENT_TOOLS` and the agent `.md` files). The text telling the resolver "edit only those files, run no git command" moves without change (R2).
- **`landing.py` in `[review] sensitive`.** The landing's prompts are built in `factory.py`'s `_land_task`, not in `landing.py`, so this change doesn't touch `landing.py`. If the diff does touch it, the review runs at full depth as configured.
- **The cached plugin carries the files.** `plugins/factory/` is the `sdlc-factory` plugin's source and is copied whole into its cache. `sdlc`'s cache carries the folder but never loads it, and `test_sdlc_loads_nothing_from_plugins` holds: `prompts/` is no scan root Claude Code knows (skills, agents, commands, hooks).
- **Pinned copies.** `RECONSIDER` stays a constant, so `tests/test_board.py` and `tests/test_metrics.py` keep pinning it.
- **No invariant needs to change.**

## Alternatives rejected

- **`str.format` placeholders.** Every literal brace in prose would have to be doubled, which invites the half-filled or `KeyError` prompt R5 exists to prevent. It also offers no `is_valid()`.
- **A marker syntax of our own (`<<round>>`).** It would need a parser and its own escape rules for nothing `string.Template` lacks.
- **One file per conditional fragment (`approve.stuck.md` …).** That makes ~45 files, and a wording edit to one task spreads across many of them. One file per task, as the intent's Outcome says, keeps a task's whole wording in one diff.
- **Logic in the files** (Jinja, `{% if %}`). It adds a dependency, and it moves the branching that `verdicts` and the tests reason about out of Python, where it can't be unit-tested the same way.
- **A host override (`.sdlc/templates/prompts/`).** It is rejected for these reasons:
  - Agents' behaviour, the eval's scores and the pinned reply shapes (`VERDICT:`, `## Evidence`, `- KEPT:`) all assume the plugin's own text.
  - An overridden prompt is untested text sent to every agent, and a host's edit to the mend wording could break `read_evidence()` silently.
  - It would also make the factory read the host's `.sdlc/` for something new.

  Not offered (R8). A later change can add it, behind a decision.
- **Comparing against the old functions kept in the test file.** That means ~370 lines of dead code living on in `tests/`. Recorded copies plus the base-branch cross-check (R3) prove the same thing.
- **Loading the prompts at import.** Each `agent` call is a fresh process anyway. Reading inside `_task()` lets a refusal come back through the normal `refusals` path rather than as an import-time crash.

## Verification

```bash
./check.sh
```
Healthy: ruff clean, `ruff format --check` clean, pytest all green (including `tests/test_prompts.py` and the unedited wording tests), and `claude plugin validate --strict` passes with `plugins/factory/prompts/` present.

```bash
uv run --group dev pytest tests/test_prompts.py -q -n auto
uv run --group dev pytest -q -m portable
```
Healthy: every case and the CRLF test pass.

The cross-check that the recordings are the old script's output (R3), run from the worktree:
```bash
mkdir -p "$TMPDIR/old164/scripts" && git archive "$(git merge-base main HEAD)" plugins/factory/scripts | tar -x -C "$TMPDIR/old164" --strip-components=2 && SDLC_FACTORY_UNDER_TEST="$TMPDIR/old164/scripts/factory.py" uv run --group dev pytest tests/test_prompts.py -q -k matches_its_recorded_copy
```
Healthy: all cases pass against the base branch's script. The R4/R5/R8 tests are skipped under the env var, since the old script has no prompt files.

```bash
grep -c 'Address every KEPT line\|keeping what both sides meant' plugins/factory/scripts/factory.py
```
Healthy: `0`.

Boundaries:
- **Always:** byte-identical prompts, files read only from the plugin, and a mismatch refused before any session.
- **Ask first:** any wording change (a later change, in the files); moving the screenshot suffix; adding `plugins/factory/prompts/**` to `[review] sensitive`; a host override.
- **Never:** edit `landing.py`, change an agent's tools, or add a dependency.

