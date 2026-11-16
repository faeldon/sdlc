---
id: 068
slug: retro-module
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 068 — Move retro's history readers out of sdlc.py · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. R1. `scripts/retro.py` defines these 37 names, and `scripts/sdlc.py` defines none of them:
   - `prose_metrics`, `_release_of`, `_evidence`, `_product`, `COMPARED`, `_stop_target`;
   - `metrics_summary`, `_prompt_report`, `_extra_report`, `_no_findings`, `_add_findings`,
     `_in_change_summary`;
   - `DROPPED_COST`, `dropped_cost`, `CLOCKS`, `process_views`, `RETROS`, `report_rel`, `_hm`,
     `_table`;
   - `render_report`, `retro_report`, `rankable_entries`, `_rework`, `retro`, `_change_rows`,
     `_kind`, `_line_counts`;
   - `_architecture`, `bugs_retro`, `_bug_paths`, `_on_paths`, `_review_at`, `cmd_retro`,
     `RERANK_KEYS`, `register_drift`, `cmd_retro_commit`.

   It also takes the five constants only that code reads (`RATE_MIN_CHANGES`, `ARCH_LOOKBACK`,
   `EVIDENCE_TIMEOUT`, `EVIDENCE_LIMIT`, `UNMEASURED`), and the loading of `scripts/indicators.py`,
   which only retro uses. A test parses both files and fails if any of these names is defined in
   `sdlc.py` or missing from `retro.py`.
2. R2. `sdlc.py` keeps everything status, release, close and the product doc's reader call, and
   those commands' output doesn't change:
   - `retro_due`, `next_up` and its helpers;
   - `doc_items`, `direction_items` and `product_items`;
   - `retrospectives`, `last_retrospective` and `_release_tags`;
   - `closed_changes`, `dropped_changes`, `_change_base` and `_days_between`.
3. R3. `sdlc.py retro`, `retro --report` and `retro --metrics` print byte for byte what the base
   branch's script prints over the same repo, except `prose.sdlc_py_lines`, which counts `sdlc.py`
   and so falls by the lines moved. An acceptance check in `checks.md` runs both and
   diffs them. `retro-commit` commits the same four paths with the same refusals, and the existing
   `retro-commit` tests pass with only their lookup changed.
4. R4. `retro.py` reads `sdlc.py`'s names when it runs, not as copies taken at load. A test
   replaces a name on the loaded `sdlc` module and shows that `retro.retro()` calls the replacement.
   The existing stand-in for `_change_base` keeps working unchanged.
5. R5. `retro.py` is loaded only by `sdlc.py`, by path from `PLUGIN_DIR / "scripts"`, like
   `metrics.py`. It has no PEP 723 block, no `__main__` and no `sys.path` edit. `sdlc.py retro`
   runs under `uv run --script` from a copy of the plugin's folder (R3's check proves this).
6. R6. The static guards cover `retro.py`:
   - `tests/test_windows.py`'s `SCRIPTS` lists it;
   - `test_no_git_call_names_main_itself`, `test_no_literal_work_path_in_the_script` and
     `test_only_the_named_steps_push` read `sdlc.py` and `retro.py` both.

   Each guard is shown to reach the new file. A planted violation in a copy of `retro.py` fails
   it.
7. R7. Tests reach the moved names only as `sdlc.retro.<name>`. `sdlc` has no attribute named
   after a moved function (R1's test checks this too). Tests that patched `sdlc.EVIDENCE_LIMIT` or
   `sdlc.EVIDENCE_TIMEOUT` patch `sdlc.retro` instead.
8. R8. `scripts/sdlc.py` shrinks by at least 1,000 lines from 9,481, and `./check.sh` passes,
   including the `portable` tests.
9. R9. `AGENTS.md`'s Retrospectives paragraph names `scripts/retro.py`. It says how the file
   reaches `sdlc.py`'s names, and that it is loaded by path but isn't pure like `metrics.py`. The
   indicators sentence names `retro.py` as the code that runs git and hands it the text.
   `docs/REFERENCE.md` changes only where it names a moved function's file.

## Design

- **The handle.** `sdlc.py` gets `_load_retro()` beside `_load_metrics()` and binds the module as
  `retro`, as `metrics` and `indicators` are bound. Right after loading, it sets `retro.sdlc` to an
  object whose `__dict__` is `sdlc.py`'s own `globals()`.
  - Every lookup goes to the live module dictionary. A `monkeypatch.setattr(sdlc, …)`, which writes
    that same dictionary, reaches retro.
  - `sys.modules` can't be used for this: the tests load `sdlc.py` without registering it, and
    under `uv run --script` it is `__main__`.
- **Inside `retro.py`:**
  - calls between moved functions stay plain names;
  - every call to a name that stays in `sdlc.py` becomes `sdlc.<name>`. The 60 names are `_git`,
    `_sh`, `load_config`, `closed_changes`, `inbox_entries`, `template_path`, `metrics`, `_lean`,
    `CHANGE_FOLDERS`, `RETRO_PREFIX` and the rest;
  - the third-party modules it uses (`frontmatter` and the like) are imported at the top of
    `retro.py`. They are already installed, because it only ever runs inside `sdlc.py`'s process.
- **Calls from `sdlc.py`:** `main()` dispatches `retro` and `retro-commit` to `retro.cmd_retro` and
  `retro.cmd_retro_commit`.
- **The move itself:** code moves verbatim apart from the `sdlc.` prefixes, so the review can read
  it as a move (the plan says how to show that).
- **Edge cases:** `cmd_retro`'s `metrics: bool` parameter shadows the `metrics` module inside that
  function only. It already did, and the module is reached as `sdlc.metrics` in `retro.py`, so no
  shadowing remains. `retro.py` is never reached without `sdlc.py` having loaded it; it has no
  entry point of its own.
- **Unchanged:**
  - the own-script handoff, which already fires on any edit under `scripts/`;
  - close's `_handoff` and `landing_reach`, which already treat `scripts/` as one unit;
  - how the plugin's cached copy carries it, as the whole `scripts/` folder.

## Contracts touched

- **Load by path, never import** (Architecture: trackers, metrics). It stays inside: `retro.py` is
  loaded with `spec_from_file_location` from `PLUGIN_DIR`, exactly as `metrics.py` is.
- **`metrics.py` and `indicators.py` stay pure, with no import of `sdlc.py`.** Unchanged.
  `retro.py` is a third kind: loaded by path but reading `sdlc.py`'s names. `AGENTS.md` says so
  (R9), so nobody takes it for one of the pure files. This is a new kind of file in `scripts/`. It
  isn't an invariant changing, but it is worth agreeing on.
- **The Windows rules** (`tests/test_windows.py`): the moved code is unchanged, and R6 puts the
  file under every check.
- **No git call names `main`; every work path comes from `work_rel()`:** these are kept, and R6
  extends both guards.
- **Only `_push()` pushes:** retro never pushes. R6 extends the guard so it never can unnoticed.
- **`retro-commit` commits only its files and refuses as strictly as before:** R3.
- **The PEP 723 block stays the one dependency list:** R5. `retro.py` declares none.
- **No literal `main` and no home paths in tests:** R3's check uses `git archive` on the base
  branch into a temporary folder.

## Alternatives rejected

- **A pure `retro.py`, handed its data like `indicators.py`.** It would rewrite 60 dependencies into
  parameters and change every signature. That is a redesign, not a move, and it can't be read as
  one at review.
- **A third shared file for the names both use.** That is two boundaries at once, the larger one
  through everything status and close rely on. It could come later, if this split pays off (M14).
- **Re-exporting the moved names from `sdlc.py`.** It keeps the test diff small, but every function
  would have two names, and the next change would edit one and test the other.
- **Copying `sdlc.py`'s names into `retro.py`'s namespace at load.** A test's stand-in set after
  loading would never reach retro, and it would silently test the wrong code.
- **`import sdlc` inside `retro.py`.** `sys.path` differs between `uv run --script` and the tests,
  and under `uv run` the script is `__main__`, so an import would run `sdlc.py` a second time.
- **Moving `next_up`, `retro_due` and the direction and product readers too.** Status, release and
  the product doc's reader call them on every run. They are status's code, not retro's.

## Verification

- `uv run --group dev pytest -q tests/test_retro.py tests/test_bugs.py tests/test_nits.py
  tests/test_windows.py tests/test_sdlc.py tests/test_work_folder.py tests/test_skills.py` passes.
- `./check.sh` exits 0, with the same test count plus R1's, R4's and R6's new tests.
- `checks.md`'s acceptance check:
  - it extracts the base branch's `scripts`, `templates`, `guide`, `defaults` and `.claude-plugin`
    into a temporary folder with `git archive`;
  - it runs both scripts' `retro`, `retro --report` and `retro --metrics` from the change's
    checkout;
  - `diff` prints nothing.
- `wc -l scripts/sdlc.py` reports at most 8,481.
