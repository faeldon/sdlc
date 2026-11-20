VERDICT: PASS

## Notes

**Trust boundaries checked.** Five record files in the change's folder are untrusted, because the builder (Edit, Write, Bash), the resolver (Edit, Bash) and any session in the worktree can write them. Their readers decide whether a change lands: `land` checking for forged records, `land_verdict()`, the train's `_read_gates()` and `_read_builds()`, `hand_gate_state()` and the approver's gate clearance. The trusted side is a ledger in the git common dir, which only the script writes.

**STRIDE, briefly:**
- **Spoofing / Tampering:** a record written by hand is now refused at each of those readers.
- **Repudiation:** the ledger only grows and is never rewritten, so older genuine versions stay vouched.
- **Information disclosure:** a ledger line holds a folder name, a record path and a hash. No secrets or output.
- **Denial of service:** records from changes already in flight are refused until rerun, which D2 and D4 already cover. A lock that won't free up gives up after 30s with a refusal and no write.
- **Elevation of privilege:** see the Medium findings below.

**Medium:**
- **The protection is weak against an agent that has Bash.** `plugins/factory/agents/builder.md:5` and `resolver.md:5` both grant `Bash`, and the builder runs `factory.py` itself. One shell command can append a valid line to `$(git rev-parse --git-common-dir)/sdlc-factory-records.jsonl`, with a sha256 of the forged file. It could also call `factory._vouch()` directly. The spec accepts this limit ("A write into the common dir goes through the harness's permission mode"), and the docs mention it. But the README's "An agent editing the change's worktree can't forge one" reads as if no agent can. Fix: in the README, REFERENCE.md and the land SKILL.md lines, say plainly that an agent whose Bash can reach the git common dir can still forge a record. The change stops a stray or careless write, not a determined agent with a shell.
- **The writer checks the file early and reads it again much later** (`factory.py` `cmd_gate()` ~3313–3358, `sdlc.py` `cmd_gate()` ~3341 and ~3393). `_unvouched_refusal()` runs before the slot wait and the check run. That gap can be long: the round-1 gate here waited 977s and ran for 255s. Afterwards `earlier` is read again from disk with no check. A file swapped in during that gap has its forged earlier attempts vouched along with the genuine new one. With Bash this adds nothing new, so it's only Medium. Fix: when reading `earlier`, call `vouched()` again (or hash the text you just read and compare it to the ledger), and refuse if the file changed under the run.

**Low / Info:**
- `vouched()` reads with `read_text`, which turns lone `\r` into `\n`, while the writer hashes the text in memory. A record whose text held a lone `\r` would read back as unvouched. That would wrongly refuse a genuine record (availability), not let a forgery through. The gate's tail goes through `splitlines()`, which removes lone `\r`. The accept record's lines come from `sdlc.py accept` output and I didn't confirm they're cleaned the same way. Consider hashing with `newline=""` on read and normalising `\r\n` only.
- D3 and D5 (`build/land-<n>.checks.md` left unprotected) are open defaults, so I don't raise them again. One point for whoever answers: a forged `CHECKS: HARMLESS` lets a changed `checks.md` run unattended under `train --run`. That is command execution on the host. It's the same class of hole as this change closes, so I'd recommend a seed, not "leave it out" with no follow-up.

- NIT: plugins/factory/README.md: "An agent editing the change's worktree can't forge one" overstates the protection when the builder and resolver have Bash. Say that it protects against the Edit and Write tools, not against a shell that can reach the git common dir {docs S med}
- NIT: plugins/factory/scripts/factory.py:3358: check again that `earlier` is vouched when it's read after the run, not only before the slot wait {robustness S med}

**What is done well:**
- Each record is vouched before it's written, so a crash between the two leaves a hash no file holds, never a genuine record left unvouched.
- A missing or unreadable ledger vouches nothing, and a garbled line is skipped.
- Each ledger line is tied to its change folder and record path, so a record copied to another change or path is refused.
- The train stops before copying any attempt from a forged record, and `land_verdict()` makes a forged record a stop that can never be mended.
- The writers refuse to add to a record they can't vouch for, before running anything.
- No secret, key or command output goes into the ledger.

**What I checked and ran:**
- Read `intent.md`, `spec.md`, `decisions.md`, the full diff of `factory.py`, `landing.py`, `factory_records.py` and `sdlc.py`, and the doc diffs.
- Read the `tools:` lines of the builder and resolver agents.
- `build/round-1.gate.md` shows GATE: PASS.
- Ran `uv run --group dev pytest -q tests/test_records_ledger.py`: 6 passed.
