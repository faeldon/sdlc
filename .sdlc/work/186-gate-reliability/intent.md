---
id: 186
slug: gate-reliability
tier: 1
impact: none
stage: shipped
created: 2026-11-19
opened: 2026-11-19T12:59Z
updated: 2026-11-19
shipped: 2026-11-19
idea: [2026-11-19-45, 2026-11-19-46]
depends_on:
serves: [O3]
---

# 186 — The gate fails only on the code

> Stage 1: why this change is worth making, in its originator's words. Read by `/sdlc:spec` at
> Tier 2, or by plan mode at Tier 1; `/sdlc:status` counts the open questions not yet struck.

## Problem

The gate failed 181's first round on nothing in 181's code, and cost a builder's fix run and a
second nine-minute gate. Seed 2026-11-19-45: "`tests/test_board_browser.py::test_the_drawer_holds_focus_and_returns_it_to_its_card`
failed in 181's round-1 gate with no error in the record's tail, and passed when rerun alone:
likely flaky under a loaded gate." Seed 2026-11-19-46: "`tests/test_adoption.py` needs network (uv
fetches PyPI deps for `uv run --script`); a gate with no DNS fails two of its tests. A skip or cache
when offline would keep the gate about the code." With four builds sharing the machine and the
network down for a few minutes, both struck the same gate.

## Outcome

- The drawer focus test passes under a loaded gate (`pytest -n auto` beside other gates), or waits
  on the state it asserts instead of on time.
- With no network, `tests/test_adoption.py`'s two tests skip with a reason that names the network,
  or run from a warmed `uv` cache, so a red gate means the code.
- **Moves O3:** a factory run no longer stops or reworks for a gate that failed on its machine.

## Affected

- **Area:** the test suite.
- **Files & components:** `tests/test_board_browser.py`, `tests/test_adoption.py`, and their
  fixtures.
- **Downstream:** every gate in this repo; nothing a host receives.
- **Contracts:** none; `check.sh` keeps no tolerance for "no tests collected".

## Constraints

- A skip names its reason in `pytest -rs`, and never hides a failure the code caused.
- The adoption tests still prove a missing dependency fails when the network is up.

## Open questions

- Is the drawer test's flake a timing wait or a real focus race in the board?

## Approach

Find why the drawer test fails under load (run it under `-n auto` beside a loaded suite) and wait
on the focus state, not a delay. Make the adoption tests detect an unreachable package index and
skip with that reason, or point `uv` at a cache the suite warms once.
