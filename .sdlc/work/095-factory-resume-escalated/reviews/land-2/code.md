VERDICT: PASS

The rebase resolution holds: I found no conflict markers, and the full suite passes (1986 tests).

## Notes
- **`.sdlc/work/inbox.md`:** the diff against `main` removes only seed 2026-11-17-16, this change's own idea. The entries from base (-10, -19 and -22 to -25) are intact. The 2026-11-17-11 nit is left to base's retirement.
- **`AGENTS.md`:** base's rewritten map from 090 is kept whole, including the `runs/mended` / `preamble()` wording. This change adds its restart rule to the factory paragraph in the same terse style. The `decision.md` / `decision-<n>.md` rule matches the spec (R13).
- **Rest of the diff:** the code, skill, tests, README and REFERENCE edits are unchanged by the rebase. Only the two conflicted files needed resolving, and I found no sign the rebase altered the rest.
- **Done well:** the resolution is minimal and sticks to base's "each rule said once" style, pointing detail to `plugins/factory/README.md`.
- **Ran:** `uv run --group dev pytest -q -n auto` (1986 passed), plus a grep for conflict markers in `AGENTS.md`, the inbox and `plugins`. I did not rerun `./check.sh` myself and relied on the builder's reported run of it in `build/land-2.md`.
