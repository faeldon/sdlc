# Notes

> What the build left undone on purpose: each `- [ ]` is a cleanup or a refactor noticed on the
> way, not this change's.

- [x] `factory.py resolve` without `--onto` still rebases onto the base branch: no skill runs it → seed: 2026-11-18-44
  that way now (the land skill always stacks with `--onto`), and only the register-conflict tests
  in `tests/test_land.py` exercise it. Fold it into `--onto <base>` or drop it once those tests
  are rewritten over a train.
- [x] After `resolve --continue`, the landing agent's reply (`build/land-<n>.md`) and the → seed: 2026-11-18-45
  `runs/land-resolved` marker stay uncommitted until the close amends them, as before the train;
  staging them with the other mid-rebase records (`RESOLVE_RECORDS`) would leave the tree clean
  after every stack.
- [x] `tests/test_train.py`'s `_drive()` and `tests/test_land.py`'s `_land_train()` both drive a → seed: 2026-11-18-46
  train as the skill does; one helper in a shared test module would do.
