DECISION: ESCALATE

**Why:** All 29 live nits are built and tested, and every round-1 reviewer gave PASS with no Critical or High finding open. The gate is green (`./check.sh`, 4145 passed). One open default remains, D1. The build made a code change to `scripts/retro.py` that the spec did not list, and it concerns which host repos are read. I treat that as scope and policy, so I can't settle it. The diff also touches the sensitive path `scripts/closing.py`, so D1 can't be carried to the landing with `CONFIRM`.

**Open items:**
- None. Every reviewer gave PASS. Two style NITs (docs, code) say `plugins/factory/skills/autopilot/SKILL.md:99` runs past the file's wrap width.

**Decisions to confirm:**
- ESCALATED: D1: `_read_hosts()` in `scripts/retro.py` now skips a host that `hosts.local` both lists and `!`-excludes, so it is never read. That is a change to what the retro reads, which the spec's Design did not list. It is consistent with 208 R3, but whether it belongs in this change or in a separate one is a scope call only the person can make.
  - OPTION: skip it — matches 208 R3 ("never read"), and R15's test passes. `listed` drops by one for such a line.
  - OPTION: leave the code and drop R15's read assertion — no code change, but an excluded host is still read, against 208 R3.
  - WHY: R15 asks for exactly this, and 208 R3 already says an excluded repo is never read.

**Other reasons to escalate:**
- ESCALATED: look: `scripts/closing.py: fix_trailers(), origin_trailer()` — both now catch `(OSError, ValueError)` instead of `Exception`. The path is in `[review] sensitive`, and a coding error there now stops a close. The spec names this and says a git or read failure still gives `[]`.

**For the person at ship:**
- Look first at the `closing.py` `except` clauses and the `scripts/retro.py` `_read_hosts()` skip. The spec's Contracts touched names the `closing.py` edit as expected and holds the change for the person for it.
- Next, `preflight --preview`. It now exits 1 when given `--context`, `--nits`, `--bugs`, `--closing` or `--split`. The old `test_preflight_preview_lists_findings_paths_and_stamp` was changed to call `--preview` alone, because it used to pass `--context --closing 12`. Ship's skill passes no flags with `--preview`.
- Next, the autopilot skill's single-quoting rule for `--goal`. Its bash blocks, `allowed-tools` and WAIT are unchanged.
- No published interface needed prior approval beyond what the spec lists.

- IMPACT: patch — nothing anyone receives gains a feature; the changes are robustness and test fixes, plus stricter refusal of flags that `preflight --preview` used to ignore.

**Undone items:** `notes.md` does not exist, so nothing is undone.

**Recovery:** the prompt names no irreversible paths, so there are no `RECOVER:` lines.
