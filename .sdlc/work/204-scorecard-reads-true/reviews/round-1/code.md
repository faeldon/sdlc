VERDICT: PASS

I read the diff and the gate record (`build/round-1.gate.md`, GATE: PASS). I ran no tests of my own. This is a Tier 1 change, so there is no `spec.md`; I reviewed against the intent's Outcome and the plan.

- **Workarounds `unknown`:** it now carries `n` and `missing_because`, and its count is null when the window has no commit, as in the other blocks. The tests in `test_retro.py` cover both.
- **Lead rows by way:** a way that closed no change now reads `no <way> change in the window`, through one `_no_way()` that the escape rate shares. The R5 test and its expected note were updated to match.
- **Surface keys:**
  - `_code_reads()` and `_key_readers()` count a key as used when a command or skill that reads it ran in the window. The scan is read-only and cached.
  - Each reading is stated explicitly. Over-counting reads is the safe side for a retire list, and a key only written is not counted as read.
  - `UNSEEN_READ_WHY` stays `unmeasured`, never `unused`, and is never a retire candidate, which holds the intent's constraint.
  - `test_every_key_has_a_reader` pins that the scan reaches every key in `CONFIG_KEYS`.
- **Decisions:** I read D1 and D2 and agree with both defaults, so I raised no decisions.
- **Docs:** `docs/REFERENCE.md` was updated for all three changes. `docs/FEATURES.md` doesn't state the key rule, so it needs no edit.

## Notes
- NIT: docs/REFERENCE.md:1344: the line `restored \`no register entry added in the window\`. A greyed block's note…` is now over-long after the reflow; rewrap it {docs S low}
- Done well:
  - The scan is documented as erring towards `used`.
  - The tests cover each read shape: subscript, `.get`, bound name, parameter handoff and method.
- Tests and commands run: none of my own; I relied on the gate record.
