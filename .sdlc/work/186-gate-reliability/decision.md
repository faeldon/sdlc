DECISION: READY

**Why.** Both outcomes in the intent are built and tested. Adoption tests that can't reach the network now run from uv's cache, or skip with a reason that names the network. The builder reproduced the drawer test's failure (a slow poll hitting a 10s wait) and replaced the wait with a single bound that only stops a hang. Round 1 passed in both the code and behaviour reviews, the gate is green (3309 passed, exit 0), and nothing in the reviews says the intent was wrong. The only open default is a test timeout, and the intent's own Approach answers it.

**Open items**
- None open. The code reviewer's three nits are recorded in `findings.md` as F1–F3, and none blocks the change.

**Decisions to confirm**
- No blocking decisions are unticked.
- SETTLED: D1: The intent's Approach says to "wait on the focus state, not a delay" and its Outcome says the test "waits on the state it asserts instead of on time". So the bound only has to stop a real hang. The builder showed that the 10s wait was the failure (polls held 11s fail with `Timeout 10000ms exceeded`) and that the 120s `PATIENT` bound passes. Round 1's behaviour review checked that `set_default_timeout(PATIENT)` is the file's only time limit, and both reviewers agreed with this default. It changes only how long this repo's own test waits: nothing a host receives, and no scope, policy, cost or interface question.

**For the person at ship**
- **`tests/test_adoption.py`:**
  - Look first at the `_uv()` fallback around line 65. When the run fails, it retries `--offline` from uv's cache, then skips. Check that the skip fires only when uv's error says it couldn't fetch the package index, so a missing dependency still fails with the network up. The builder checked this by hand.
  - F1: the skip test matches uv's exact wording, "network was disabled". If a future uv changes that text, the gate goes red on the network again.
- **`tests/test_board_browser.py`:** `PATIENT = 120s` replaces the 10s poll wait and Playwright's 30s defaults. A truly broken board now takes up to two minutes to fail.
- **Published interfaces:** none touched. The change is test files only, and the intent says *Contracts: none*.

**Release impact**
- IMPACT: none — only this repo's own tests changed, and nothing a host receives is different.

**Undone items**
- UNDONE: `tests/test_train.py`'s `by()` runs `uv run --script` on a copy of the plugin at a new path, as the adoption tests did, so a gate with no network can fail it the same way. It could share the adoption tests' `_uv()` (offline from uv's cache, else a skip naming the network). → seed: test_train's by() should share _uv()'s offline fallback
