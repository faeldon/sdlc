DECISION: ESCALATE

**Why:** Both outcomes are built and tested, and every reviewer passed round 1 with no Critical or High finding open. The gate is green. Two things hold it back from READY. D1 widens the change past its intent into program-running options, and only the person can settle that. Because the diff touches `landing.py`, which is sensitive, I can't carry any default to the landing with CONFIRM.

**Open items:**
- None unresolved. The nits (the comment on `--filter-magic-label`, the "makes ugrep" wording for GNU grep, and a pin for `-d dereference-recurse` used as a pattern) are low and optional.

**Decisions to confirm:**
- ESCALATED: D1: Refusing `--filter`, `--pager`, `--view`, `--save-config`, `--config` and `---FILE` goes beyond the intent, which names only link-following options. It is a scope call on a sensitive file. The security reviewer reproduced `--filter` running a program, and every reviewer accepted the default, so the person can approve it quickly.
  - OPTION: refuse them — closes the hole where a single-quoted `--filter` runs any program, and only tightens the list. It is wider than the intent.
  - OPTION: links only, as the intent says — the narrowest change, but `grep --filter='*:…'` still runs programs on a train when the host's grep is ugrep.
  - WHY: `--filter` ran `touch` in a test, and a check that runs a program is worse than one that follows a link.
- SETTLED: D2: The intent's open question names `--dereference-recurse` and the Approach covers "any sibling ugrep option the plan finds that follows links". The security review confirmed ugrep rejects abbreviated `-d` values, so refusing the bare word fails safe. The only cost is that a check grepping for that literal needs a person.

**Every other reason you escalate for:**
- None beyond D1.

**For the person at ship:**
- Look first at the new grep refusals in `plugins/factory/scripts/landing.py` (`GREP_FOLLOWS_LONG` and `GREP_REFUSED_LONG`, around lines 816–925) and at `test_a_train_names_a_readiness_refusal_as_its_cause` in `tests/test_train.py`.
- No published interface is touched, and `landing.py` is sensitive only by path.

- IMPACT: none — the read-only list only gets stricter and a test is added; nothing a holder of the previous release receives changes.

**Undone items:**
- UNDONE: pre-existing: plugins/factory/scripts/landing.py:816: `GREP_FOLLOWS` refuses `-O` (BSD's follow-links flag) for every grep, so ugrep's harmless `-O EXT` (search by file extension) is refused too. This is overly strict, not a hole. → seed: Let ugrep's `-O EXT` pass the read-only grep check while BSD's `-O` stays refused
