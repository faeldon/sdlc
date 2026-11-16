# 068 — Move retro's history readers out of sdlc.py · notes

## Sizes

- `scripts/sdlc.py`: 9,481 lines before, 8,328 after (−1,153).
- `scripts/retro.py`: 1,227 lines, new.

## How the move was done

A throwaway script in the session's scratchpad, never committed, did the move by `ast`:
- it took each moved node with its comments above;
- it prefixed each read of a name staying in `sdlc.py` with `sdlc.`;
- it wrote `retro.py` and rewrote `sdlc.py`.

Ruff then pruned the unused imports on both sides and reflowed the lines the prefixes pushed past
100 characters. Three lines were wrapped by hand.

## What the tool printed, and the hand fixes

- **`cmd_retro`'s `metrics`:** the tool skipped it, as it should. It is the function's bool
  parameter, not the module.
- **`_load_indicators()`:** it reads `Path(__file__).with_name("indicators.py")`, since it runs
  while `retro.py` loads, before `sdlc` is bound.
- **`metrics_summary`'s `allowance` default:** it read `sdlc.CONFIG_KEYS` when the function was
  defined, which crashed at load. It is now `None`, resolved inside, with the same value. The tool
  didn't flag it, because it checked module-level statements and not defaults. `AGENTS.md` now
  says that a default in `retro.py` can't read `sdlc`.
- **`prose_metrics`'s `sdlc_py_lines`:** it counted `Path(__file__)`, which after the move would
  have been `retro.py`'s 1,227 lines. It now counts `sdlc.PLUGIN_DIR / "scripts" / "sdlc.py"`, so
  the field keeps its meaning. Its value falls from 9,481 to 8,328, the one figure the move exists
  to change.

## Spec deviation

- **R3** said `retro`'s output is byte-for-byte the base's. It is, except for
  `prose.sdlc_py_lines` (above). The acceptance check compares `retro --report` byte for byte, and
  the JSON of `retro` and `retro --metrics` with that one field deleted. Run by hand: all three
  match.
- **The check archives `skills` and `agents` too:** `prose_metrics` reads the skills from the
  plugin's folder, so a copy without them reports none.

## Tests

- **Retargeted:** 49 lookups in `test_retro`, `test_bugs`, `test_nits`, `test_factory` and
  `test_windows` now read `sdlc.retro.<name>`. The `EVIDENCE_*` patches target `sdlc.retro`.
- **New:**
  - `test_retro_lives_in_its_own_file`;
  - `test_retro_reads_sdlcs_names_when_it_runs`;
  - `test_retro_has_no_entry_point_of_its_own`;
  - `test_the_source_guards_reach_retro_py`;
  - `test_the_work_path_guard_reaches_retro_py`.
- **Guards extended:**
  - the `main`, `gh` and work-path guards are parametrized over `sdlc.py` and `retro.py`;
  - the push guard reads both;
  - `test_windows.py`'s `SCRIPTS` lists `retro.py`.
