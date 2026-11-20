VERDICT: PASS

## Notes

Landing round 1 has no Critical or High findings. Both fixes the person asked for are in the code and the docs.

**Trust boundaries.** This is the same boundary as round 1. Gate, build and accept records in the change's folder can be written by any agent in the worktree, so they are untrusted. The ledger `sdlc-factory-records.jsonl` lives in the git common dir, and only the script writes it, so it is the trusted side. This round adds one more way in: the host's `[commands] check`, or something running beside it during the slot wait, could rewrite the record between the first check and the append.

**The fix the person asked for in `cmd_gate`**
- `plugins/factory/scripts/factory.py` `cmd_gate`: after the slot and the run, it calls `_unvouched_refusal()` again. This happens before `read_gate_file(path)` counts the attempts and before `earlier` is read. On a refusal it returns before `_vouch()` and before `write_text`, so the forged file stays as it is and the ledger gets no line. The message's `.replace("nothing was run", "this attempt was not recorded")` works, because `_unvouched_refusal()` ends with "nothing was run". This applies to round, landing and `--build` records alike.
- `scripts/sdlc.py` `cmd_gate`: the hand gate has the same check again after the `try/with slot` block, using `_hand_vouched(checkout, folder, path)`, and it also returns before `_vouch` and the write.
- Both new tests make the check command itself copy a forged record over the real one. That is the attack in question, and each test checks that the file is unchanged and the ledger has no new rows.
- What the fix closes: the "forged attempts get vouched along with a real one" problem from round 1, for any rewrite made before the second check.

**The doc fix the person asked for.** The README, REFERENCE.md and the land SKILL.md all now say the ledger protects against the Edit and Write tools, not against a shell that can reach the git common dir. This was round 1's Medium, and it is done.

**Medium / Low / Info**
- Info: a small window is still open between the second `vouched()` read and the `earlier = path.read_text(...)` read: one read, hash, then a second read. A rewrite inside that window would be vouched along with the new attempt. To use it, something would have to be timing its writes against a running script, and anything that can do that has a shell, which the docs now say is out of scope. A full fix would read the file once, check that text against the ledger, and build `earlier` from the same text. That is cheap, but nothing needs it now.
- Info: `build/land-1.gate.md` opens `GATE: PASS`, and the builder's run of `factory.py check` reports 3619 passed and 29 skipped. I did not rerun the gate.

- NIT: plugins/factory/scripts/factory.py:2896: the ledger comment still says "guards against a write in a worktree"; reword it to match the docs (Edit and Write tools, not a shell that can reach the git common dir) {docs S low}

**What I checked:** the `0eae32e...HEAD` diff of `scripts/`, `plugins/` and `docs/`; both `cmd_gate` bodies in full; `_unvouched_refusal`, `vouched`, `_vouch`, `_hand_vouched` and `factory_records.vouched_in`; the new hand-gate test; the land-1 report and its gate record; round 1's `security.md` and `decisions.md`.
