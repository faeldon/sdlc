---
id: 153
slug: risky-code-in-its-own-modules
kind: spec
created: 2026-11-18
updated: 2026-11-18
---

# 153 — Close, push, the lock and the landing live in modules the deep review can name · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code: `depth()` (`factory.py`) and ship's `risk_paths()`
(`sdlc.py`) read `[review] sensitive` from the base branch, never the change's checkout
(`_review_list()`, `test_the_sensitive_list_is_the_base_branch_s_not_the_change_s`).
`_changed_paths()` counts added files, so a diff that creates a listed path deepens the run.
`retro.py` already shows the pattern to copy: it is loaded by `spec_from_file_location`, bound
through `_Names(globals())`, and its tests reach it as `sdlc.retro.<name>`. `_handoff()` runs
`main / "scripts" / "sdlc.py"`, and `PLUGIN_DIR` comes from that file's own path, so a handed-off
close loads the sibling module from the same checkout. Nothing a host configures or sees names a
moved function, so nothing here is a shim and `.sdlc/deprecations.toml` gets no entry.

1. **R1. `scripts/closing.py` holds close, the push and the main lock.** It defines the lock
   family (`_msvcrt_lock`, `_msvcrt_unlock`, `_flock_lock`, `_flock_unlock`, `_lock`, `_unlock`,
   `_lock_path`, `_LOCK_DEPTH`, `LOCK_HELD_ENV`, `_lock_depth`, `_main_lock`, `_inherit_lock`),
   `cmd_close` and each helper that only close's code calls (by the rule in R3: `_close_commit`,
   `_drop_record`, `_handoff`, `HANDOFF_ENV`, `_cleanup_plan`, `CLEANUP_TIMEOUT`,
   `_carries_others`, `_ff_deletions` and the like), and `_push` and `_push_plan`. `sdlc.py`
   defines none of them. `test_close_push_and_the_lock_live_in_closing` fails if any is defined in
   `sdlc.py`'s AST, or missing from `closing.py`'s.
2. **R2. `plugins/factory/scripts/landing.py` holds the landing.** It defines the commands
   `land` (`cmd_land`, `cmd_land_close`, `cmd_land_fix`), `land-check` (`cmd_land_check`),
   `train` (`cmd_train` and its `_train_*`, `_run_*`, `run_lock`, `train_*` and `TRAIN_*` /
   `RUN_STEPS` state), `resolve` (`cmd_resolve` and its rebase helpers) and `land-verdicts`
   (`cmd_land_verdicts`, `land_verdict`), and each helper that only those call. `factory.py`
   defines none of them. `test_the_landing_lives_in_landing` fails the same way R1's does.
3. **R3. The line is a rule, and a test holds it.** A name moves when it is one of R1's or R2's
   named entries, or when only moved code calls it. A name that any code left in the script
   calls stays there, and the module reads it as `sdlc.<name>` or `factory.<name>`.
   `test_the_line_between_script_and_module_holds` (once for each pair) parses both files. It
   fails on a function defined in a module, other than R1's or R2's named entries, that the script
   reaches as `closing.<name>` or `landing.<name>`, which means it should have stayed. It also
   fails on a function defined in the script that only the module calls, which means it should
   have moved.
4. **R4. Loaded by path and bound live, never imported.** `sdlc.py` loads
   `PLUGIN_DIR / "scripts" / "closing.py"` when it is imported (`_load_closing()`, built like
   `_load_retro()`) and sets `closing.sdlc = _Names(globals())`. `factory.py` loads
   `landing.py` from beside itself, using a `_Names` class of its own, and sets
   `landing.factory = _Names(globals())`. Neither script has an `import` statement naming
   either module. Commands are routed to `closing.cmd_close` and `landing.cmd_*`. The existing
   tests that patch a name that stays (`test_land.py`'s and `test_factory.py`'s
   `setattr(factory, "_sdlc", …)` and `"_claude"`, which now drive moved code) pass unchanged.
   That shows a stand-in still reaches the moved code. `test_the_modules_are_loaded_by_path` fails
   on an `import closing`/`import landing` or a `sys.path` edit in either script.
5. **R5. Neither module does anything when it loads, or has a path of its own.** No `__file__`
   (`landing.py`'s train runs `factory.FACTORY_SCRIPT`, never itself), no PEP 723 block, no
   `if __name__`, and no default argument or module-level statement that reads `sdlc.` or
   `factory.`, which are still unbound at that point. `land_question()`'s
   `moves=DEFAULTS["land"]["moves"]` becomes `moves=None`, filled in from `factory.DEFAULTS` in the
   body, and the result is the same. `test_the_modules_read_nothing_while_loading` parses both
   files and fails on any of these.
6. **R6. Behaviour is unchanged.** The whole suite passes. The diff under `tests/` changes only
   how a moved name is reached (`sdlc.X` → `sdlc.closing.X`, `factory.X` → `factory.landing.X`,
   including `monkeypatch.setattr` targets such as `_handoff`, `_push_plan` and `_run_group`), and
   which sources a guard reads (R8), and adds R1–R5's and R9–R10's tests. It edits no expected
   value. The reviewer checks this by reading `git diff <base> -- tests/`.
7. **R7. No command's interface or output moves.** `--help` for `sdlc.py`, for `factory.py`,
   and for each of `close`, `publish`, `release`, `new`, `inbox-commit`, `land`, `land-check`,
   `train`, `resolve` and `land-verdicts` is byte-identical before and after (Verification).
   No `Sdlc-*` trailer, JSON key or refusal text changes. The tests that pin them (`test_archive`,
   `test_push`, `test_release`, `test_register_lands`, `test_land`, `test_train`, `test_resolve`)
   pass with only R6's edits.
8. **R8. Every source guard reads the new modules.** `closing.py` is added to `CORE` in
   `tests/test_sdlc.py` and `tests/test_work_folder.py`, to the sources
   `test_only_the_named_steps_push` concatenates, and to `SCRIPTS` in `tests/test_windows.py`.
   `landing.py` is added to `SCRIPTS` there too. `test_the_source_guards_reach_closing_py`, built
   like `..._reach_retro_py`, plants a `refs/heads/main`, a `["gh", …]` call, a literal `work/` and
   a second `git push` in `closing.py`'s text, and asserts each guard finds it. Without these
   additions, moving the code out of `sdlc.py` would silently move it out of reach of every guard.
9. **R9. `factory.py` and `landing.py` never import `sdlc.py`.** The rule was held by
   convention and is now tested. `test_the_factory_never_loads_sdlc_py` fails on an `import sdlc`,
   or on a `spec_from_file_location` naming `sdlc.py`, in either file. `_sdlc()`'s subprocess run
   of `sdlc_path()` stays in `factory.py` and is allowed.
10. **R10. The deep review names both modules, and only them.** The base branch's
    `.sdlc/config.toml` lists `"scripts/closing.py"` and `"plugins/factory/scripts/landing.py"`
    under `[review] sensitive`, with a comment saying why. `test_the_landing_code_is_reviewed_in_depth`
    (`tests/test_factory.py`) reads this repo's own `[review]` table into a change's base config.
    A diff touching either module makes `verdicts` return `depth == "full"`, with that path in
    `sensitive`. A diff touching only `scripts/sdlc.py`, or only
    `plugins/factory/scripts/factory.py`, makes it return `depth == "light"`. A companion assertion
    checks that `sdlc.risk_paths()` with the same list names both modules and not `sdlc.py`, which
    is what ship's security pass reads. Removing either listing, or renaming either module without
    updating the list, fails the test.
11. **R11. This change is reviewed at full depth.** The listing in R10 is on the base branch
    before this change's build starts (resolved below). Because the diff creates both files, the
    first `verdicts` of the build returns `depth: full`, with both paths in `sensitive`, and ship's
    preflight names them as risky paths. If the build's first `verdicts` says `light`, that is a
    stop, not something to carry on with.
12. **R12. Each module's docstring is its contract, and the map says where the code lives.**
    Each docstring says what the module holds, what the rule in R3 is, how it is bound and what it
    may call, that it is listed in `[review] sensitive` and why, and which invariants it keeps
    (only `_push` pushes; the lock span; no `sdlc.py` import). The changes to AGENTS.md are:
    *Modules loaded by path* adds both modules and their bindings; *Closing* and *The factory* say
    the code is in `closing.py` and `landing.py`; *Invariants*' push line names `closing.py`.
    CONTRIBUTING.md's *Layout* table gets a row for each module. `plugins/factory/README.md` changes
    wherever it says the landing is in `factory.py`. `sdlc.py context` lists these docs, and ship
    checks them.

## Design

**Two modules, one per script, each a pure move.** Each module copies what `retro.py` does and adds
nothing to it.

`scripts/closing.py` opens with its docstring, then `from __future__ import annotations`, its own
stdlib imports (`os`, `subprocess`, `threading`, `json`, `re`, `contextlib.contextmanager`,
`pathlib.Path`) and `sdlc = None`. Every function moves with its body unchanged except that each
call to a name that stayed is rewritten as `sdlc.<name>`: `sdlc._git`, `sdlc.work_rel`,
`sdlc.main_root`, `sdlc._config_at`, `sdlc.register_plan` if it stays, `sdlc._script_cmd`,
`sdlc.tracker`, `sdlc.metrics`, and so on. Calls between functions inside the module stay bare.
`sdlc.py` defines `_load_closing()` beside `_load_retro()` and binds `closing = _load_closing()` at
import. Its remaining callers change as follows:

- `claim()` and `cmd_inbox_commit()` call `closing._main_lock(...)`.
- The hand gate's slot code calls `closing._unlock(fd)`. Its own `_try_lock` stays, because it
  belongs to the hand gate.
- `cmd_release` calls `closing._push_plan`/`closing._push`, and `cmd_publish` calls
  `closing._push`.
- The `close` subcommand routes to `closing.cmd_close`.

The `.call(` text inside `closing._push(` still contains `_push(`, so
`test_only_the_named_steps_push`'s caller set stays `{cmd_publish, cmd_close, cmd_release}` once
`closing.py` is in its source (R8).

`plugins/factory/scripts/landing.py` is built the same way, with `factory = None`. `factory.py`
gets a `_Names` class (three lines, its own, since it never imports `sdlc.py`) and
`_load_landing()`, which loads `Path(__file__).resolve().parent / "landing.py"` under the spec name
`factory_landing`. Calls from the landing to code that stayed become `factory.<name>`:

- running sdlc: `factory._sdlc`, `factory.sdlc_path`
- git and reading the change: `factory._git`, `factory.find_change`, `factory._base`
- the gate: `factory._run_check` (through `cmd_gate`, which stays)
- landing records and steps: `factory._record_land`, `factory.read_land_step`,
  `factory.land_step_text`
- review risk: `factory.risk_paths`, `factory._sensitive`
- the train's subprocesses: `factory.FACTORY_SCRIPT`

`main()`'s dispatch calls `landing.cmd_*`.

**What stays, and why.** The rule in R3 decides most of it. These are named because someone will
ask:

- `cmd_drop`, `cmd_release`, `cmd_publish`, `_config_at`, `_script_cmd` and `_own_script` stay in
  `sdlc.py`, because code outside close calls them.
- `factory.py` keeps `cmd_agent` (including its landing tasks `_land_task`/`_land_diff`), `_claude`,
  `cmd_gate` (including `--land`), `_run_check`, `cmd_fresh`, the landing-step record format
  (`LAND_STEP`, `_record_land`, `read_land_step`, which the board's pinned copies follow) and
  `risk_paths`/`depth`. That keeps AGENTS.md's single-place rules ("`factory.py agent` is the one
  place the factory runs `claude`", "`_run_check()`, the only place it runs a host's command")
  literally true. It also leaves the board's pins on the same module they pin today.
- The cost: a change to `gate --land` or to an agent's landing prompt stays light. That is the
  intent's own line (land, train, resolve), and widening it would be a decision of its own.

**State lives in one place.** `_LOCK_DEPTH` (thread-local) and `LOCK_HELD_ENV` exist only in
`closing.py`, so the reentrant hold and the handed-off hold count in one table. Each test file that
loads `sdlc.py` under its own spec name gets its own `closing` instance, just as each gets its own
`retro`.

**Edge cases.**

- *This change's own close.* `main`'s pre-move `sdlc.py` runs close and merges. `_handoff()` then
  runs the merged `scripts/sdlc.py`, which loads `closing.py` from beside itself. The two
  implementations behave the same, so the resumed close finds what the first one did. That handoff
  is the first real exercise of the move.
- *The factory landing this change.* `sdlc_path()` runs the `sdlc.py` of the factory's own
  version, and through it that version's `closing.py`. They are the same files.
- *A cached install.* Both plugins' caches carry `scripts/` and `plugins/factory/scripts/` whole,
  so the sibling files are present. `test_sdlc_loads_nothing_from_plugins` is unaffected.
- *Windows.* `closing.py` keeps the lock's platform imports inside the functions that need them, as
  `sdlc.py` does now, and both modules join `SCRIPTS` (R8).

### Boundaries

- **Always:** the move is mechanical. Each function body is unchanged apart from the
  `sdlc.`/`factory.` prefix, the R5 default argument and the dispatch lines. The whole gate passes
  at every commit.
- **Ask first:** about anything that would change a function's behaviour, output or name; about
  moving anything outside R1–R2 and the R3 rule; and about the precursor listing in R10/R11 before
  the build starts.
- **Never:** a re-export alias in either script, a new command or flag, a change to a trailer or
  a refusal text, or a shim entry.

## Contracts touched

- **Modules loaded by path.** The rule is "loaded by path, never imported, bound to a live view of
  the script's globals". Both modules follow it exactly (R4), and the map lists them (R12).
  `landing.py` is the factory's first module of this kind. Its binding is named `factory`, never
  `sdlc`, so nobody reads it as a link to `sdlc.py`.
- **`factory.py` never imports `sdlc.py`.** Kept, and now tested for both files (R9). The pinned
  copies (`risk_paths`, `_sh`, `_utf8_streams`, the record parsers, `held_entries()`'s copies) stay
  pinned. Where a copy moves into `landing.py` under R3, its pin test reaches it as
  `factory.landing.<name>` and still compares the same two functions.
- **Only the named steps push.** `_push()` is still the one push, never forced, and its callers are
  still `cmd_publish`, `cmd_close` and `cmd_release`. Close and release still go through
  `_push_plan()`. The test now reads `closing.py` too (R8), so the invariant is kept, not loosened.
  AGENTS.md's wording "`sdlc.py`'s one git push" becomes "the core's one git push, in
  `closing.py`'s `_push()`". That rewords a fact the move changes; it is not a policy change.
- **Closing.** `_main_lock()` is held from the merge to the `Close` commit, `_carries_others()`
  refuses, `_handoff()` passes `LOCK_HELD_ENV`, and `close_cleanup` comes from `_config_at()` on
  the base branch. The code moves with each of these unchanged, and the tests that pin them pass
  (R6).
- **The base branch: `git.base`.** `test_no_git_call_names_main_itself` reads `closing.py` (R8).
- **`.sdlc/work/` paths come from `work_rel()`.** `test_no_literal_work_path_in_the_script` reads
  `closing.py` (R8).
- **Core never calls `gh`.** The `_gh_calls` guard reads `closing.py` (R8).
- **The scripts run on Windows.** Both modules are in `SCRIPTS` (R8).
- **The factory: landing is the one place it commits.** This stays true. It now means `landing.py`,
  and the map says so (R12).
- **`[review] sensitive` is read from the base branch, so a change can't lighten its own review.**
  This design leans on that rule instead of working around it. The listing goes on the base first
  (R11). No change to how the list is read.
- **Tiers.** This change is Tier 2 by `.sdlc/SDLC.md` ("how a change's folder is committed,
  archived or removed"). Risk never changes a tier, and this change doesn't try to.

No invariant needs to change.

## Alternatives rejected

- **List `scripts/sdlc.py` and `factory.py` as sensitive.** Nearly every run would go to full
  depth (60 and 50 commits this month). The light depth would be pointless, which is the problem
  the intent describes.
- **Function-level sensitive patterns** (`scripts/sdlc.py::cmd_close`). This needs new matching in
  `risk_paths()` and in both of its pinned copies, plus a mapping from diff hunks to functions that
  breaks on every rename. It is a feature, not a move.
- **Three modules from `sdlc.py`** (`close.py`, `push.py`, `lock.py`). Close takes the lock and
  pushes, so the three would call each other through three bindings, and the sensitive list would
  get three entries where one says the same thing. One module per script is the smallest thing the
  review can name. Splitting later is a move of its own.
- **Re-exports in the scripts** (`cmd_close = closing.cmd_close`). A test's stand-in on
  `sdlc.cmd_close` would not reach the module's own calls, so the alias looks like a seam and isn't.
  It also leaves two names for one function. Tests reach moved names on the module, as retro's do.
- **Loading the modules lazily, as `board.py` is loaded.** `new` and `inbox-commit` need the lock on
  every run, and tests reach names as attributes. An eager load costs one file read.
- **Importing via a `sys.path` edit.** AGENTS.md rules it out: `uv run --script` and the tests put
  different directories on the path.
- **A flag for a person to ask for full depth on this run.** It would be a new feature, against the
  intent's "a move only" constraint. A one-line listing on the base gets the same result with
  existing code.
- **Moving `cmd_release`/`cmd_publish`, `gate --land` or the agents' landing tasks too.** None is in
  the intent. Moving `agent` or `_run_check` would break AGENTS.md's single-place rules for
  `factory.py`. Each could be a seed of its own if review evidence shows it is needed.

## Verification

Before the build starts, check that the base branch lists both paths:

```bash
git show "$(uv run --quiet --script scripts/sdlc.py config | jq -r .git.base)":.sdlc/config.toml \
  | grep -E '"scripts/closing.py"|"plugins/factory/scripts/landing.py"'
```

Healthy: both lines printed. During the build, `factory.py verdicts 153` reports `"depth": "full"`,
with both module paths in `"sensitive"` (R11).

The gate and the Windows subset:

```bash
./check.sh
uv run --group dev pytest -q -m portable
uv run --group dev pytest -q tests/test_factory.py -k reviewed_in_depth
uv run --group dev pytest -q tests/test_sdlc.py tests/test_work_folder.py tests/test_windows.py \
  tests/test_skills.py -k "guard or push or loads or line_between or read_nothing or never_loads"
```

Healthy: all green, with the new tests named in R1–R5 and R8–R10 among those run.

The code is where the move put it:

```bash
git grep -nE '^def (cmd_close|_main_lock|_push|_push_plan|_lock_depth)\b' scripts/sdlc.py
git grep -nE '^def (cmd_land|cmd_train|cmd_resolve|_run_loop)\b' plugins/factory/scripts/factory.py
```

Healthy: both print nothing.

Interface unchanged (R7). Unpack the base into a scratch directory and compare help text:

```bash
old=$(mktemp -d); git archive <base> scripts plugins templates defaults guide | tar -x -C "$old"
uv run --quiet --script "$old/scripts/sdlc.py" close --help > "$old/close.txt"
uv run --quiet --script scripts/sdlc.py close --help | diff "$old/close.txt" -
```

Do the same for `sdlc.py --help`, `publish`, `release`, `new`, `inbox-commit`, and for
`factory.py --help`, `land`, `land-check`, `train`, `resolve` and `land-verdicts`. Healthy: every
`diff` prints nothing.

Tests changed only in how they reach names (R6):

```bash
git diff <base> -- tests/
```

Healthy: every hunk is a name reached through `.closing.`/`.landing.`, a source list gaining a
module, or a new test. No expected value is edited.

The change's own close prints a report with `ran` naming the merged script and no `refusals`. That
is the handoff from the pre-move `sdlc.py` to the post-move one.
