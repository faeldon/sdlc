# Notes

- [x] The build skill's summary of `start`'s `ui` (`serve`, `shoot`, `paths`) doesn't name `fixture`; the README does. → seed: 2026-11-17-67
- [x] `tests/test_board.py::test_the_board_fixture_shows_every_card_state` takes about 30s on a cold `uv` cache (two `sdlc.py gate` runs); a `--no-gate` path in `build.sh` isn't worth it yet. → seed: 2026-11-17-68
