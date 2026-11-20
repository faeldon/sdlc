DECISION: READY

**Why:** All three outcomes are built and tested. Both reviewers returned PASS in round 1, the gate is green, and the plan explains each choice the build made. The one remaining finding is a docs rewrap nit. It is minor and does not block landing.

**Open items:**
- NIT (code reviewer): `docs/REFERENCE.md:1344` has a line left over-long after the reflow. This is cosmetic.

**Decisions to confirm:**
- SETTLED: D1: `plan.md` specifies the scan as following each command's calls and reads, and `notes.md` records that it over-counts towards `used`. The code reviewer agreed. Nothing in the intent's constraints is touched.
- SETTLED: D2: `plan.md` names skill files' `section.key` mentions as readers. The intent's outcome says the retire list keeps only keys nothing read, and skills read `commands.build`, `build_when`, `close_list`, `worktree_setup` and `docs.review`. The code reviewer agreed. The live retire list then holds no config keys.

**For the person at ship:**
- Look first at `scripts/retro.py`: `_code_reads()`, `_key_readers()` and `_states()`. This is where a key is judged used, unused or unmeasured.
- The current window recorded no commands, so `git.base` reads `unused` there with 0 uses. Earlier windows count it as used, which keeps it off the retire list. The behaviour reviewer found this is not a fault of the change.
- No published interface is touched.

- IMPACT: patch — a retrospective's scorecard and retire list read more accurately. Nobody holding the previous release has to do anything differently.

- UNDONE: The scan's reach could follow only calls, not every mention of a name, if the surface's key share should separate keys a command reads on every run from keys it reads on one branch. → seed: Surface key scan follows calls only, to separate always-read keys from branch-read keys
