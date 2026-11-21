DECISION: ESCALATE

**Why:** The build looks sound. Round 1 is all `VERDICT: PASS`, `./check.sh` is green with 3694 passed, and R1–R13 each have a test that would fail without them. The run stops here because the builder reports R14 and R15 can't be tested. Both are prose, so the gate can't show whether the skill's wording or the insight agent's reading rule actually behaves as the spec says. A person has to look at that wording.

I did not open `spec.md`, `plan.md`, `build/round-1.md` or the changed code. I judged from `decisions.md`, the three round-1 reviews and the gate record. There is no `notes.md`.

## Open items
- NIT (code reviewer): `scripts/retro.py: _discover` doesn't resolve install paths before comparing them to the listed and excluded paths. R9 says to resolve them.
- NIT (code reviewer): `scripts/retro.py: _scrub` checks string values only, not dict keys. It leaks nothing today, and it needs a comment so a later change doesn't add a host-derived key.
- NIT (test reviewer): `tests/test_retro_hosts.py:329` never lists a path under `.claude/worktrees/`, so R3's `own` skip isn't exercised.
- NIT (test reviewer): `tests/test_retro_hosts.py:325` excludes a path that doesn't exist, so it would pass even if an excluded host were still read.
- NIT (test reviewer): `tests/test_retro_hosts.py:426` doesn't compare the report's indicators block, which R12 covers.

## Decisions to confirm
- SETTLED: D1: R9 says discovery runs only when a list exists, and the behaviour reviewer saw `sdlc.py hosts` with no list print the create-the-file line, run no discovery and exit 0.

## Other reasons I escalate
- ESCALATED: look: `skills/retro/SKILL.md` direction-pass and reply wording (R14) — only judged by eye. `tests/test_skills.py` just confirms the skill runs no new command.
- ESCALATED: look: `agents/insight.md` reading rule (R15) — a prose rule with no test.
- ESCALATED: look: `scripts/retro.py: hosts_figures()` and `sdlc.py hosts` — retro now reads other repos' git history in the plugin's own repo. That is the privacy contract, and `hosts` is deliberately outside `READ_ONLY` and `ALLOW_RULES`. The person should confirm the scope is what they approved in the intent and spec.

## Reconsider the approach
The loop didn't fail to converge. The stop comes from R14 and R15 being untestable as written. The next step I'd take is to rewrite R14 and R15 into checkable forms:
- **R14:** split it into a structural part a test can pin, such as the skill naming the `## Hosts` section, saying the figures are never pooled and having no new command, plus a plain wording part the person approves by eye.
- **R15:** mark it as reviewed by eye, or move the rule into the data. For example, put a fixed "not pooled with this repo" field in the `INSIGHT_DATA` hosts slice, which a test can assert.

Neither needs a rebuild of the scripts. After the person reads the wording, the three NITs on tests and `_discover` can ride along as small follow-ups.

## For the person at ship
- Read the `skills/retro/SKILL.md` diff and the `agents/insight.md` diff first, since they are the untested parts.
- Then read `scripts/retro.py: hosts_figures()`, `_scrub` and `_discover`, and `cmd_hosts` in `scripts/sdlc.py`.
- Confirm `.gitignore` carries `.sdlc/hosts.local`. The behaviour reviewer checked this with `git check-ignore`.
- I found no published interface the change touches that the person approved earlier.

- IMPACT: minor — someone running retro in the plugin's own repo can now opt in to a host-repo Hosts section. Other repos see nothing change.

## Undone items
None. There is no `notes.md`.

## How to recover
- RECOVER: templates/retro.md: fix forward: the template only adds the `## Hosts` section. A revert removes the section from later reports, but reports already written and committed keep it. A follow-up change would remove or reword it.
