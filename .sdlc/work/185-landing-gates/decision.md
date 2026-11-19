DECISION: ESCALATE

**Why.** All four reviewers passed round 2. Every requirement from R1 to R19 has a named test that exists and passes. R20 is covered by a check in `checks.md` and by two reviewers' greps. Round 1's one CHANGE (a `TypeError` in `land-checks` when `checks.md` has been removed) was fixed in the right place, `checks_clearance()`, and a test now covers it. The change can't be called READY yet because two of the defaults are the person's to decide. D1 widens the read-only allow-list policy beyond R5. D3 is the published "host command only behind a prompt" contract that the spec itself says "needs explicit approval".

**Open items**
- None. Round 2 is `VERDICT: PASS` from code, test, security and behaviour.
- A leftover note from security round 2, not a CHANGE: GNU grep accepts a shortened long option, so `--der` or `--dereference` gets past the exact `--dereference-recursive` refusal at `landing.py:876`. It is Low, because it also needs the approver to judge the changed check HARMLESS. It is worth a look at ship.
- A leftover note from test round 2: `factory.py:4431` `checks_sha(folder)[:16]` is safe only because of the guard in `_land_task`.

**Decisions to confirm**
- No blocking decisions are unticked.
- ESCALATED: D1: this is a policy question about which commands a train may run without the person. R5 is the allow-list the person approved in the spec, and checking glued short-option values goes beyond it. The change only makes the list stricter, and code round 1 and security round 1 both agreed with it. Still, the allow-list is policy the person set in the spec, so changing it is their call.
- SETTLED: D2: R17 is about `_not_already_made()`'s own refusal lines, and those are all short. Its case loop in `tests/test_land.py` passes. The only lines that can run past 160 characters are the person's own command, echoed by `read_evidence()`, which the build loop shares. Truncating them would hide the command the refusal is about. Code round 1 agreed with the default, and test round 1 accepted R17's assertion as written.
- ESCALATED: D3: the edit to `AGENTS.md`'s factory paragraph rewrites a published contract: "a host's command runs only behind a prompt" becomes "behind the yes, or cleared by both the approver and the read-only list". The spec's *Contracts touched* says this edit "needs explicit approval". Only the person can say whether approving the spec was meant to give that approval.

**For the person at ship**
- Look first at `plugins/factory/scripts/landing.py`:
  - `read_only_command()`: the scanner, the program list, the grep symlink flags, and the shortened `--der` gap above.
  - `checks_clearance()`: the allow-list is checked before the approver's record is read, which is what R8 depends on.
  - `_run_plan()` and `_clearance_now()`: the recheck before `accept` runs (R9).
  - `_train_build()` and `_read_builds()`.
- Then look at the `land-checks` plumbing in `factory.py`: `_land_task()`, `cmd_agent()` filing the reply under `Judged:`, and `holds()`. Also read the new `plugins/factory/prompts/land-checks.md`.
- `cmd_gate --land --build` and `_base_command()` read `[commands] build`, `build_when` and `[review] sensitive` only from the base branch. That is the published config surface, and the approved spec names it (R11, R12, *Contracts touched*).
- `AGENTS.md`'s factory paragraph, `plugins/factory/README.md` and `skills/land/SKILL.md` now state the new rule, as the spec's *Contracts touched* words it. Whether that wording is approved is D3.
- Code round 1 also left nits on line wrapping in `AGENTS.md` and `SKILL.md`.

- IMPACT: minor — a host using the factory can now land without clicking through acceptance checks it already approved, and gets its `commands.build` run once at the train's tip when a change calls for it. Nothing that already worked has to change.

**Each undone item's disposition**
- UNDONE: The land skill's frontmatter `description` still lists what a landing runs without the build at the tip or the approver's judgement of changed checks; Step 3 and the steps list say both. A wording pass on the description alone, kept out of this change. → seed: Land skill description names the build at the tip and the approver's check judgement
- UNDONE: pre-existing: plugins/factory/scripts/landing.py:2180: gate/build/accept records are trusted by the hash they state, which any agent that can write in the change's folder can write; a script-side signature or a record kept outside the tree would close it → seed: Landing records that an agent in the change's folder can't forge

The second item is a gap in what the landing trusts, not something already broken that can be shown going wrong. None of the guide's severity words (`high`, `med`, `low`) fits it, so I'm carrying it as a seed rather than filing it as a bug.
