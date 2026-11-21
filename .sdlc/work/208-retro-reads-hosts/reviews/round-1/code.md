VERDICT: PASS

I found no Critical or Required problems. I read the spec and the full diff of `scripts/retro.py` and `scripts/sdlc.py`, and the docs, skill, agent and template changes. I skimmed `tests/test_retro_hosts.py` by test name only and ran no tests. Per the gate record `build/round-1.gate.md`, `./check.sh` passed.

## Notes
- NIT: scripts/retro.py:`_discover`: the install's `project` strings are compared to the resolved listed and excluded paths without being resolved first. A symlinked or differently spelled install path (for example `/var` against `/private/var` on macOS) could show an already-listed repo as unlisted. Run `Path(p).resolve().as_posix()` on each install before comparing, as R9 says. {robustness S med}
- NIT: scripts/retro.py:`_scrub`: it checks string values only, not dict keys. The keys today all come from fixed vocabularies, so nothing leaks. A comment saying so would stop a later change from adding a host-derived key. {docs S low}
- Done well:
  - Each host record is cut down to the vocabulary before anything sums it, and `_scrub` is a second guard behind that.
  - `hosts` is built in `report_figures()` and reaches `retro` and `retro --insights` from there.
  - `INSIGHT_EVERY` and the new `INSIGHT_DATA` slices match the R13 table.
  - Discovery runs only when a list exists, and a failed `plugin list` reports `unmeasured` without its reason text.
  - `cmd_hosts` is not in `READ_ONLY` and does not appear in `ALLOW_RULES`.
  - `dropped_changes()` gained `drop_at` without changing existing fields.
  - The docs (AGENTS.md, CONTRIBUTING, REFERENCE, FEATURES, the `cmd_retro` docstring and the module docstring) now say retro reads outside the repo in the plugin's own repo.
- Tests and commands: none run by me. The gate result is the one recorded in `build/round-1.gate.md`.
