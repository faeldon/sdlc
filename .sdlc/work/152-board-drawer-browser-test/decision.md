DECISION: ESCALATE

**Why.** Every reviewer passed this change in round 1: code, test, security and behaviour. The gate is green, with 2833 passed and 28 skipped. Each of the intent's three outcomes has a test or an acceptance check, and the reviewers ran the browser test green against Chromium. I'm escalating only because D2 and D3 are the person's own open questions in `intent.md`, and the builder answered them by default. Both decide how far the test reaches and what the gate prints, so they are scope calls only the person can make.

**Open items**
- No CHANGE is still open. Every finding in `findings.md` is a nit or pre-existing, and all are recorded:
  - F1, F4 and F5: the header comment on `check.yml:3` is too long. Raised by code, security and test.
  - F2: no skip note in `./check.sh`. Raised by code.
  - F6: the test takes about 49s. Raised by test.
  - F3: the workflow has no `permissions:` block (pre-existing). Raised by security.

**Decisions to confirm**
- SETTLED: D1: `plan.md` says why the test serves the board in-process instead of through `serve.sh`: the OS picks the port, so parallel test workers don't race for it, and the server is shut down in a `finally`. That is what the intent's constraint requires ("stops the server however the test ends"). The code, security and test reviews of round 1 each confirm the server binds `127.0.0.1` on a port the OS picks and always shuts down.
- ESCALATED: D2: "Chromium alone, or WebKit too" is an open question the person left in the intent. Adding WebKit would mean a second, larger browser download in CI and on contributors' machines, so it is a scope and cost call. The person has to answer it even though the intent's Approach names Chromium.
- ESCALATED: D3: whether `./check.sh` should say when the browser test skips is the person's other open question in the intent. It is a call about what the gate shows every contributor on every run. The code reviewer also raised it again as F2.

**For the person at ship**
- Look first at `tests/test_board_browser.py`. Check that the `chromium` fixture skips only on "Executable doesn't exist" and re-raises every other launch error. Then check the step that writes `notes.md`, waits for a poll to rebuild the cards, and then expects focus back on the card with the same `data-change`.
- Then look at the one new step in CI's Linux job in `.github/workflows/check.yml`, which is on the sensitive list. It runs `playwright install --with-deps --only-shell chromium` and uses apt through sudo.
- Then look at `uv.lock`. Security noted, as Low, that playwright 1.65.2 was published only four days before the review. Pinning that version, or setting uv's `exclude-newer`, is optional.
- Last, the long header comment on `check.yml:3` is a one-line re-wrap that three reviewers flagged.

- IMPACT: none — Playwright is only in this repo's `dev` group, and only the tests, CI and CONTRIBUTING.md changed. Nothing a host installs or runs is different.

- UNDONE: pre-existing: .github/workflows/check.yml:13: no `permissions:` block; set `permissions: contents: read` so a compromised dev dependency running in CI can't use a write-scoped token → seed: Limit CI's GITHUB_TOKEN to contents: read in check.yml

I filed the undone item as a seed, not a bug: nothing has broken yet, and the guide's severity words describe something that is broken.
