I set `gate_jobs = 1` and turned autopilot on in `.sdlc/factory.toml`, the only file the change touches. Both acceptance checks failed before the edit and pass after it. The settings take effect only once the change lands on main, and no autopilot run has started.

**What changed:**
- **The setting:** `gate_jobs = 2` → `gate_jobs = 1`.
- **Autopilot:** a new `[autopilot]` section with `enabled = true` and a comment naming M25. Its other keys keep their defaults, and `guards` stays unset, so nothing is loosened.
- **The header comment:** no longer says "two gates at once". It now says one gate runs at a time because two filled the swap (round median 158.5 → 261.5 seconds). It says this lasts until M24's 2026-11-22-38 removes the wait, and that both settings are for M25's run.

There's no `plan.md`: this is a Tier 1 change touching one file, so the intent's Approach is the plan.

**Checks:** `checks.md` has two acceptance checks, since no test reads this repo's own `factory.toml`:
1. The file parses with `gate_jobs == 1` and `autopilot.enabled is true`.
2. The first 12 lines name M25, "two gates at once" appears nowhere, and no `guards` line is set.

**Tests run:** `tests/test_nothing_local.py`, the test that scans every file's text, passed 8 of 8. I didn't run the full suite; the gate runs it next.

**Not done:** the intent's last two outcomes (`factory.py config` showing `gate_jobs` as 1, and `autopilot --preview` showing `"enabled": true`) can only be checked from the main checkout after close.

**Open question for the M25 run:** the intent asks whether the run takes -50 and -51 while they sit in "decide", which autopilot never takes. That's a question for the run, not this build. It needs an answer before `--begin`, or those two need to be made ready first.

Nothing was left in `notes.md`.

- DECISION: [default] Leave `enabled = true` on main after the M25 run until a later change turns it off? Going ahead with leaving it on: this change adds no off-switch.
  - OPTION: leave it on, a later change turns it off — this change stays the one-file settings edit it set out to be; autopilot stays enabled between runs, but nothing runs until someone runs `--begin`
  - OPTION: a follow-up change turns it off right after the run — nothing is enabled that nobody planned; one more small change
  - OPTION: turn it off in the retrospective that reads what the run landed — the decision is made with the evidence; the setting stays on until then
  - WHY: the intent leaves this open, and autopilot still needs a person to approve its single WAIT before it begins, so leaving it on starts nothing.
- UNTESTABLE: none

## Evidence

$ uv run --quiet --group dev python -c 'import tomllib, sys; c = tomllib.load(open(".sdlc/factory.toml", "rb")); sys.exit(0 if c.get("gate_jobs") == 1 and c.get("autopilot", {}).get("enabled") is True else 1)'; echo "exit: $?"   (before the edit)
exit: 1

$ head -12 .sdlc/factory.toml | grep -q 'M25' && ! grep -q 'two gates at once' .sdlc/factory.toml && ! grep -q '^guards' .sdlc/factory.toml; echo "exit: $?"   (before the edit)
exit: 1

$ uv run --quiet --group dev python -c 'import tomllib, sys; c = tomllib.load(open(".sdlc/factory.toml", "rb")); sys.exit(0 if c.get("gate_jobs") == 1 and c.get("autopilot", {}).get("enabled") is True else 1)'; echo "exit: $?"   (after the edit)
exit: 0

$ head -12 .sdlc/factory.toml | grep -q 'M25' && ! grep -q 'two gates at once' .sdlc/factory.toml && ! grep -q '^guards' .sdlc/factory.toml; echo "exit: $?"   (after the edit)
exit: 0

$ git status --short
 M .sdlc/factory.toml
?? .sdlc/work/234-autopilot-first-run/
exit: 0

$ uv run --quiet --group dev pytest -q tests/test_nothing_local.py 2>&1 | tail -3; echo "exit: $?"
8 passed in 2.53s
exit: 0
