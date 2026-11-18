# Decisions

- [x] D1 (builder round 1, default): For -57, name `factory.py shots NNN --round 1 --role ui` rather than the bare `factory.py shots NNN` the intent wrote, since the bare form is refused. Going ahead unless told otherwise. → settled by the approver: factory.py's argument parser marks both `--round` and `--role` as required for `shots` (`p_shots.add_argument(... required=True)` at lines 7692–7693), so the bare `factory.py shots NNN` the intent wrote would be refused. `plan.md` records the switch to the full command. `test_preflight_passes_ui` checks the exact text, and both round-1 reviewers accepted it. The intent's aim was "names the command that takes them", and only the full form does that.
  - OPTION: full command — works when pasted as is; a longer `why` in the note and the question
  - OPTION: bare `factory.py shots NNN` — matches the intent's words; fails with a missing-argument error
  - WHY: a pointer the person can't run as written defeats -57
- [x] D2 (builder round 1, default): For -72's open question, use a generic `<term>` placeholder, not the term's kind. Going ahead unless told otherwise. → settled by the approver: per AGENTS.md (*Nothing about a project*), `.sdlc/terms.local` is "one regex per line" with no kind to name, so a per-kind placeholder would need a new file format, which the intent never asks for. The only constraint the intent sets is that a term is never quoted, and `test_a_reply_quoting_a_local_term_is_filed_as_a_placeholder` proves it, `defuse`'s JSON output included. Code's round 1 agreed.
  - OPTION: `<term>` — `terms.local` is bare regexes with no kind to name; nothing else to maintain
  - OPTION: a kind per term — reads better; needs a new format for `terms.local` that the scan would also have to parse
  - WHY: the file holds no kinds, and the intent's constraint is only that a term is never quoted
