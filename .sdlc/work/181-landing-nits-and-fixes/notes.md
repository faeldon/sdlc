# Notes

- [x] `tests/test_board_browser.py::test_the_drawer_holds_focus_and_returns_it_to_its_card` failed in 181's round-1 gate with no error in the record's tail, and passed when rerun alone: likely flaky under a loaded gate. Not this change's code. → seed: 2026-11-19-45
- [x] `tests/test_adoption.py` needs network (uv fetches PyPI deps for `uv run --script`); a gate with no DNS fails two of its tests. A skip or cache when offline would keep the gate about the code. → seed: 2026-11-19-46
