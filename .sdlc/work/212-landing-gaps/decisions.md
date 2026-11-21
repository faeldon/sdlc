# Decisions

- [x] D1 (builder round 1, default): Also refuse ugrep's `--filter`, `--pager`, `--view`, `--save-config`, `--config` and `---FILE` in an unattended check? Going ahead with refusing them unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: refuse them — closes a hole where a single-quoted `--filter` runs any program; only makes the list stricter, as the constraint allows; slightly wider than the intent
  - OPTION: links only, as the intent says — the narrowest change; `grep --filter='*:…'` keeps running programs on a train when the host's grep is ugrep
  - WHY: `--filter` ran `touch` in a test here, and a check that runs a program is worse than one that reads through a link
- [x] D2 (builder round 1, default): Refuse the bare word `dereference-recurse` even as a grep pattern? Going ahead with refusing it unless told otherwise. → settled by the approver: The intent's open question names `--dereference-recurse` and the Approach covers "any sibling ugrep option the plan finds that follows links". The security review confirmed ugrep rejects abbreviated `-d` values, so refusing the bare word fails safe. The only cost is that a check grepping for that literal needs a person.
  - OPTION: refuse it anywhere — covers `-d dereference-recurse` and bundled `-rd` without tracking which flag takes the next word; a check that greps for that exact text needs the person
  - OPTION: refuse it only right after `-d` — fewer false refusals; misses bundled forms unless the code parses short-option bundles
  - WHY: stricter and simpler, and a check grepping for that literal is rare
