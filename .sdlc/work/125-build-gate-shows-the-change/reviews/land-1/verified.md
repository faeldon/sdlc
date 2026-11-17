- KEPT: behaviour: C1: plugins/factory/scripts/factory.py:942: with no base branch (`base` is None), `check` and `sensitive` are never read, yet `build_question()` says "with no gate configured" and drops the sensitive parenthesis. This is a claim nothing verified.

## Notes
I read `start` (about lines 900–945), `behind_base()` and `build_question()`. `behind_base()` returns `base` as None when `_base()` finds nothing. In that case line 942 skips both `_base_check()` and `_sensitive()`, so `check` is None and the gate clause falls into its "no gate configured" branch. `start` adds no refusal there. Other commands already refuse with "no base branch: set [git] base in .sdlc/config.toml" (for example line 2080), so refusing in `start` too would match them. I didn't run the tests.
