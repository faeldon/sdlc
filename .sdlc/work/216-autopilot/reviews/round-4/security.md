VERDICT: PASS

No Critical or High finding in the round-4 rework (D8, D9, D10). Nothing was kept from last round, so there was no kept change to check.

## Notes

**D8: sensitive paths are guarded by default. Done.**
- When `guards` is unset, `_default_guards()` (autopilot.py:205) now returns the policy and review docs, `[review] irreversible` and `[review] sensitive`.
- Both path lists are read from the base branch through `factory._irreversible()` and `factory._sensitive()`, so a change can't loosen its own guards.
- The config is fixed at `--begin`.
- `test_default_guards_hold_the_sensitive_paths` checks that the change's own `[review]` adds nothing.

**D9: a seed with an `Issue:` line is taken only when named, and is opened with `closes:`. Done.**
- `candidates()` (autopilot.py:312) skips a seed whose `issues` is anything but `[]` unless `--seeds` names it. That includes `None`, meaning a line that can't be read.
- `open_seed()` holds a `None` seed before any agent runs.
- `opened_intent()` writes `closes:` only from `entry_issues()`'s integers (sdlc.py:1630). Issue text can't get into the frontmatter, so there is no injection.
- With `closes:` written, the landing's `issue` signal and its risk weight work again.

**D10: what `--by autopilot` protects against. Documented as decided.** AGENTS.md, the factory README and the skill now say the marker stops a process from inheriting it by accident. They also say it is not a boundary against a same-user process that sets the marker on purpose, and that the real limit on a misled builder is its own permissions and sandbox.

**`status --json` is read-only.** It prints `next_up()`'s items and warnings and returns before any other part of `status` runs. The only field this round adds is `issues`.

**Medium: two files that hold the run's own guards aren't in this repo's `[review] sensitive`.** The list now has `plugins/factory/scripts/autopilot.py`. It still lacks:
- `plugins/factory/scripts/factory.py`, which holds `take_markers()`, `autopilot_running()`, `agent_env()`, `land-check` and the records ledger;
- `scripts/sdlc.py`, which holds `ship` and `status --json`.

A change that autopilot lands to `factory.py` can weaken the marker and lock checks for the rest of the same run, because `run_step()` runs `FACTORY_SCRIPT` fresh from the main checkout. That is D8's own reason for guarding sensitive paths. This is this repo's config choice, not a code defect. The fix is to add `plugins/factory/scripts/factory.py` to `sensitive`, and probably `scripts/sdlc.py` too.

**Low: the default guards can lose the docs if `config` fails.** If `factory._sdlc(["config"])` fails, `_default_guards()` drops the policy and review doc paths without a word. It keeps only the base-derived path lists. Better to hold the run, or warn, when `config` can't be read: guards that fail open are the wrong direction for an unattended run.

- NIT: plugins/factory/scripts/autopilot.py:211: `_default_guards()` drops the policy and review docs without a word when `sdlc.py config` fails; add a warning to `load_config`'s list, or stop at `--begin` {robustness S med}

**What I checked and ran:**
- I read the round-4 build report, `decisions.md` (D1–D11 all answered) and the diffs of `autopilot.py`, `sdlc.py`, `tests/test_skills.py` and `.sdlc/config.toml`.
- `build/round-4.gate.md` shows the gate passed (`./check.sh`, exit 0; the build report counts 3947 passed, 29 skipped).
- I ran the four D8/D9 tests (`-k "sensitive_paths or issue or real_status"`): 4 passed.
