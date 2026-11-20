# Decisions

- [x] D1 (builder round 1, default): Should a key count as read when any function a command can reach reads it, even on a branch that doesn't run? Going ahead with this unless told otherwise. → settled by the approver: `plan.md` specifies the scan as following each command's calls and reads, and `notes.md` records that it over-counts towards `used`. The code reviewer agreed. Nothing in the intent's constraints is touched.
  - OPTION: anything reachable — it errs towards `used`, which is the safe side for a retire list, and it covers the intent's "every key load_config() reads"; but most keys read as used by most commands
  - OPTION: only keys read on every run — closer to "on every run", but it needs flow analysis that a static scan can only approximate
  - WHY: the retire list must keep only keys nothing read, and a missed read would show a key the code still reads as a retire candidate
- [x] D2 (builder round 1, default): Should a skill that names a key in its files count as reading it? Going ahead with yes. → settled by the approver: `plan.md` names skill files' `section.key` mentions as readers. The intent's outcome says the retire list keeps only keys nothing read, and skills read `commands.build`, `build_when`, `close_list`, `worktree_setup` and `docs.review`. The code reviewer agreed. The live retire list then holds no config keys.
  - OPTION: yes — `commands.build`, `build_when`, `close_list`, `worktree_setup` and `docs.review` are read only by skills (ship, close, intent, spec), through `config`'s output
  - OPTION: commands only, as the Approach says — those five keys would wrongly become retire candidates
  - WHY: the outcome says "the retire list keeps only keys nothing read"
