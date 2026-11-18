# 139-landing-train — entries

## [2026-11-18-44] [idea] Fold `factory.py resolve`'s base-branch rebase into `--onto <base>`

Left undone by 139-landing-train, carried forward when it landed: `factory.py resolve` without `--onto` still rebases onto the base branch: no skill runs it that way now (the land skill always stacks with `--onto`), and only the register-conflict tests in `tests/test_land.py` exercise it. Fold it into `--onto <base>` or drop it once those tests are rewritten over a train.
See .sdlc/work/139-landing-train/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-45] [idea] Stage the landing agent's reply and `land-resolved` with `RESOLVE_RECORDS`

Left undone by 139-landing-train, carried forward when it landed: After `resolve --continue`, the landing agent's reply (`build/land-<n>.md`) and the `runs/land-resolved` marker stay uncommitted until the close amends them, as before the train; staging them with the other mid-rebase records (`RESOLVE_RECORDS`) would leave the tree clean after every stack.
See .sdlc/work/139-landing-train/notes.md in its commit.
Raised 2026-11-18.

## [2026-11-18-46] [idea] One shared test helper that drives a landing train

Left undone by 139-landing-train, carried forward when it landed: `tests/test_train.py`'s `_drive()` and `tests/test_land.py`'s `_land_train()` both drive a train as the skill does; one helper in a shared test module would do.
See .sdlc/work/139-landing-train/notes.md in its commit.
Raised 2026-11-18.
