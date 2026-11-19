# Notes

- [x] `tests/test_train.py`'s `by()` runs `uv run --script` on a copy of the plugin at a new path, → seed: 2026-11-19-75
  as the adoption tests did, so a gate with no network can fail it the same way. It could share
  the adoption tests' `_uv()` (offline from uv's cache, else a skip naming the network).
