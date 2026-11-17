DECISION: ESCALATE

**Why.** All three round-1 reviewers passed the build. The code reviewer found code and a test for each of R1–R15 and saw `./check.sh` pass with 1,937 tests. The gate record is a PASS too. I'm escalating for two reasons. First, decision D1 is still unticked. Second, the change adds a new `sdlc.py gate` command that writes, so hosts get a new public command whose name and record shape they will come to rely on.

**Open items**
- None from the reviewers: every round-1 verdict is PASS and nothing was carried over to `notes.md`.
- Optional (code reviewer): `HAND_GATE_RE` in `scripts/metrics.py` matches `scripts/sdlc.py gate` anywhere in a Bash command. A `grep` or `echo` that only mentions it would count as a `check` event.
- Optional (code reviewer): `hand_build()` returns the same hash whenever `merge-base` fails, because the path list is then empty. `trunk_refusal` makes this unlikely in practice.
- Note (ux reviewer): the reviewer asked for confirmation that factory cards never show the gate badge. The code reviewer and the builder say factory cards carry no `gate` key, and R10's test is meant to pin that.

**Decisions to confirm**
- D1: the spec's by-hand Verification steps 1–4 can't run on 091, because its own R2 rule refuses a factory folder. The build accepted fixture tests in their place: `test_board.py`'s gate, edit and read-again tests, and `test_status_marks_a_current_gate_only`. The alternative is to try the steps by hand on a separate test change built by hand.

**For the person at ship**
- **`cmd_gate()` and `hand_build()` in `scripts/sdlc.py`:**
  - The check should come from `_config_at(home, refs/heads/<trunk>)`, not from the checkout's config.
  - The paths left out of the hash should be built from `work_rel()`.
  - The digests should be taken before the check runs, and those are what `Build:` records.
- **`gate` in `OWN_SCRIPT_CMDS`:** the spec accepts that a change can alter the code that records its own gate. It says this is safe because the check command still comes from the base branch, and the record only informs the board and status. Decide whether you agree.
- **`_seen()` and `next_action()` in `scripts/board.py`:**
  - The order should be: `findings.md` first, then a current green gate, then the `build` stage.
  - A red gate should come before the `build` branch.
- **The badge in `board.html`:** it shows only when `gate.current` is true, which is the code reviewer's reading of R10. The UI reviewers' screenshots showed no hand-built card, so nobody has seen the badge rendered. Running D1's by-hand check on a test change would show it, and would check its contrast.
- **`HAND_GATE_RE` in `metrics.py`:** decide whether to anchor it before landing.

- IMPACT: minor — hosts get a new `sdlc.py gate` command, and the board and status show a hand-built change's gate as green or red, which wasn't possible before. Nothing existing changes.
