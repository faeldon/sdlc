- KEPT: security: C1: plugins/factory/scripts/factory.py:3934: a busy answer returns through `_gate_busy()` before `changed` is worked out, so a check that edits the tree and exits with `[park] exit` is parked and the edit is never flagged. The next attempt's `before` already holds the edit, so it reads `Tree: unchanged` and goes green.

## Notes
- I read `cmd_gate` and `_gate_busy` and ran nothing.
- The code matches the claim. `before` and `after` are both taken inside the slot, and `busy_of` runs after the check returns. Line 3935 returns before line 3936 computes `changed`.
- The builder should watch one thing in the fix. On `SlotWaitExpired`, the check never ran, so `before` and `after` are unbound. `changed` must be computed only when the check ran, for example by setting `before = after = {}` or `changed = []` on that path. Otherwise the fix raises `NameError` on a slot-wait expiry.
- The requested test should also check a slot-wait expiry, which is still BUSY with no `Tree:` line.
