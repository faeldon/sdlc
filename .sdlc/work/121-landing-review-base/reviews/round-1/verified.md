- KEPT: code: C1: plugins/factory/scripts/factory.py:2500: `_land_diff()` falls back to `base` (the moved tip) when `merge-base` fails, which silently brings back the bug this change removes. `_land_task` already returns a string as a visible refusal, so it can stop the round instead.

## Notes
I only read the code. `_land_diff` is used in both the land-review and verify branches, and both return a string refusal in other cases. The `merge-base` fallback is reachable only when no common ancestor exists or `base` is invalid, which is rare, but the fallback is silent and defeats the purpose of the change. I ran no tests.
