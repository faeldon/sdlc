# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The drawer test bounds only a hang, never a poll's speed

A test that proved it would hold a poll past a tight bound on every gate, about fifteen seconds
of waiting, so the bound is checked here: the page takes the patient default, and no step names a
timeout of its own.

```sh
grep -q 'page.set_default_timeout(PATIENT)' tests/test_board_browser.py &&
! grep -q 'timeout=' tests/test_board_browser.py
```
