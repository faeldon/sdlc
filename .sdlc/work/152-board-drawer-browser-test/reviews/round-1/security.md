VERDICT: PASS

## Notes

**Trust boundaries the diff touches**

- **New dev-only dependency.** `playwright>=1.49` resolves to playwright 1.65.2 and greenlet 3.5.6 in `uv.lock`, both from PyPI with sha256 hashes. Nothing on the plugin's host-facing side changes: `scripts/` and `plugins/*/scripts/` don't name it, and the new `test_no_plugin_script_names_playwright` keeps it that way. Hosts run the scripts through `uv run --script` with their own PEP 723 blocks, so this can't reach them.
- **CI's Linux job.** It gains one step: `playwright install --with-deps --only-shell chromium`. That downloads a browser build from Playwright's CDN over HTTPS, and `--with-deps` installs system packages with apt using the runner's sudo. The browser binary isn't pinned by hash in our lock; the playwright wheel fixes which build it fetches. That's normal for a CI runner that holds no secrets: the workflow uses no secrets, only runs on push and `workflow_dispatch` (no `pull_request_target`), and pushes nothing.
- **The test's server.** `board.serve(root, 0)` binds `127.0.0.1` only, on a port the OS picks, and the fixture stops it in a `finally`. It serves a scratch copy of the fixture under `tmp_path`. The browser only loads that local URL.

**STRIDE, briefly.** Tampering and elevation risk sits only in the supply chain of a dev and CI dependency, and the hashed lock limits it. There's no information-disclosure surface: no secrets and no network listener beyond loopback. Denial of service, repudiation and spoofing don't apply.

**Medium / Low**

- **Low:** playwright 1.65.2 was uploaded on 2026-11-14, four days before this review. A release that new has had little time to be noticed if it were compromised. It runs only on contributor machines and a CI runner without secrets, so the risk is small. If you want a buffer, pin the version you checked or use uv's `exclude-newer` for the lock. That's optional.
- **Info:** `check.yml` has no `permissions:` block, so the job's `GITHUB_TOKEN` gets the repo's default scope. That was already true before this change, and the new step doesn't use the token.
  - PREEXISTING: .github/workflows/check.yml:13: no `permissions:` block; set `permissions: contents: read` so a compromised dev dependency running in CI can't use a write-scoped token
- NIT: .github/workflows/check.yml:3: the rewrapped header comment runs past the file's line width {style S low}

**Done well**

- The new test enforces the "never reaches a host" rule itself.
- The server stops however the test ends.
- The skip only catches the "Executable doesn't exist" launch error. Any other launch error still fails the test, so a broken setup isn't hidden as a skip.

**What I checked:** `intent.md` and `decisions.md` (D1–D3: none are security risks); the diff of `pyproject.toml`, `check.yml`, `CONTRIBUTING.md` and `uv.lock` (only greenlet and playwright were added, all hashed); `tests/test_board_browser.py`; `board.serve`'s binding; and `round-1.gate.md`, where the gate passed.
