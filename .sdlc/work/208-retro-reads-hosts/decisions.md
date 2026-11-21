# Decisions

- [x] D1 (builder round 1, default): With no `.sdlc/hosts.local`, `sdlc.py hosts` doesn't run discovery, following R9's "discovery runs only when a list exists". It tells you to create the file, which may be empty, and rerun. Going ahead with this unless told otherwise. → settled by the approver: R9 says discovery runs only when a list exists, and the behaviour reviewer saw `sdlc.py hosts` with no list print the create-the-file line, run no discovery and exit 0.
  - OPTION: discovery only with a list — follows R9 as written, and nothing calls `claude plugin list` until you've opted in; costs one extra step (create an empty file) the first time
  - OPTION: `hosts` discovers even with no list — easier to start, and the paths only ever go to your terminal; but it bends R9 for the command
  - WHY: R9 is explicit, and an empty file is a cheap opt-in
- [x] D2 (approver round 1, look): `skills/retro/SKILL.md` direction-pass and reply wording (R14) — only judged by eye. `tests/test_skills.py` just confirms the skill runs no new command. → decided: seen
- [x] D3 (approver round 1, look): `agents/insight.md` reading rule (R15) — a prose rule with no test. → decided: seen
- [x] D4 (approver round 1, look): `scripts/retro.py: hosts_figures()` and `sdlc.py hosts` — retro now reads other repos' git history in the plugin's own repo. That is the privacy contract, and `hosts` is deliberately outside `READ_ONLY` and `ALLOW_RULES`. The person should confirm the scope is what they approved in the intent and spec. → decided: seen
