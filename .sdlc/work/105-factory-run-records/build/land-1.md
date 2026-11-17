I resolved both conflicted files and ran no git command, as asked. The repo's gate (`./check.sh`) passes after the resolution: 2125 tests passed and 9 skipped, ruff clean, plugin validation passes.

## `.sdlc/work/inbox.md`

Both sides deleted seeds from the same stretch of the register, so I kept every deletion:
- **From the base branch:** it removed seeds 2026-11-17-43 (limit how many factory gates run at once) and 2026-11-17-47 (the board serves the code it was built from). These look shipped by other changes, since the base now has `gate_jobs`.
- **From this change:** its commit removed its own seeds, 2026-11-17-42, -44 and -48, which are built here.

None of those five entries is left. I also removed the `Theme:` and `Raised` lines each conflict left behind, which no longer belonged to any entry. Entries 41, 45, 46 and 49 and everything around them are untouched, and each entry still ends with its own `Theme:` and `Raised` lines.

## `plugins/factory/scripts/factory.py`

The only conflict was in the module docstring's paragraph listing what each command writes. I merged the two versions:
- **From the base branch:** the text on `fresh` (it moves the change's branch onto the base through `sdlc.py base` and `resolve`, and commits nothing that stays), and on `gate`'s slot lock file in the git common dir.
- **From this change:** `write-spec` writing the approved draft to `spec.md`, and `agent` filing a spec draft to `runs/spec-draft.md` and its questions to `runs/spec-questions.md`, never to `spec.md`.

The code itself merged cleanly. Both sides' work is in the file: the base's `cmd_fresh` and `gate_jobs`, and this change's `split_draft`, `cmd_write_spec`, `SUPERSEDES_RE` and the readers that now use `open`.

## Evidence

$ grep -rn "^<<<<<<<\|^=======$\|^>>>>>>>" .sdlc/work/inbox.md plugins/factory/scripts/factory.py
(no output: no conflict markers left)
exit: 1

$ for n in "def cmd_write_spec" "def split_draft" "SUPERSEDES_RE = " "def cmd_fresh" "gate_jobs" "\"open\"\]"; do printf "%s: " "$n"; grep -c "$n" plugins/factory/scripts/factory.py; done
def cmd_write_spec: 1
def split_draft: 1
SUPERSEDES_RE = : 1
def cmd_fresh: 1
gate_jobs: 12
"open"\]: 5
exit: 0

$ ./check.sh
All checks passed!
213 files already formatted
2125 passed, 9 skipped in 76.49s (0:01:16)
✔ Validation passed
exit: 0
