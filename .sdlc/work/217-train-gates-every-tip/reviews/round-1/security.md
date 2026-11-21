VERDICT: PASS

## Notes

This change closes a hole where a landing could push a red base branch without telling anyone. It removes no control and adds none of its own. I found nothing Critical or High.

**Trust boundaries the diff touches**
- **The base branch's `[commands] check`.** The new `_ungated()` and `cmd_land_check()`'s `gated` both read it through `factory._base_check(main, base)`, which is `_base_command()` on the base branch. They never read the change's checkout. A change therefore can't make its own landing say "not gated", and it can't turn off the gate at the tip. This meets the constraint "never the change's own copy".
- **Tampering with gate records.** A train of one used to skip the gate. Now it goes through `_read_gates()` and the forged-records stop, so the ledger vouches for its `land-<n>.gate.md` the same way it does for a longer train. When a train of one's change opened no round, `cmd_gate --land` writes the record as `land-1`. That is the path bisection already used for a change that never moved, and the ledger covers it.
- **Pushing a red base (repudiation and integrity).** Dropping the `stacked == pre` shortcut means every train runs the check on its committed tip before any close and push. That covers both escapes the intent describes: a file the build's gate saw only as untracked, and a `fresh` rebase onto a newer base. The red-tip path still ejects as before, with `reset --keep`. There is no new force and no new destructive step.
- **Information disclosure.** `ungated` is a fixed sentence holding the base branch's name. It carries no secret, path or host data.

**Low / Info**
- When the base names no check, the question says "not gated". That approval can still approve itself (`by=auto`) if no change carries a risk signal, so an ungated landing can go through with no person seeing it. That is the host's choice (it has no gate to run), and the report now says so.

**What I checked**
- I read `intent.md`, the full diff (`landing.py`, `factory.py`, the `SKILL.md` edits and the docs), and `_base_check` / `_base_command` together with the rest of `_train_gate`.
- I read `build/round-1.gate.md`: it is green (`./check.sh`, exit 0). I didn't run the gate myself.

**Done well:** the fix removes a shortcut instead of patching the tree comparison that failed. The not-gated state is worked out fresh from the base branch every time and never stored in the train's state, so it can't go stale.
