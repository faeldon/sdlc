# 196 — Plan

> Tier 1, written because the Approach reaches four files. The intent's Approach is the spec.

## Files to change

- `plugins/factory/scripts/factory.py`
  - `read_evidence()`: a `## ` line ends the section only when no command is open (after an
    `exit:`, or before the first `$ `), or after a blank line unless the open command is a read
    that has printed. Otherwise it is the open command's output.
  - `_land_task()`: the `train-resolve` prompt adds one `deleted` part per modify/delete
    conflict, from `deleted_sides()`. (The builder's `resolve` task is left as it is: the landing
    loop never runs it; see notes.md.)
  - `cmd_decisions()`: `by_alts` is built only from entries with two or more options (nit
    2026-11-20-8), and a raise matches by its alternatives only then too.
  - New `deleted_sides(root)`, beside `_conflicted()` (in `factory.py`, since `_land_task()` calls
    it: `tests/test_modules.py`'s line between script and module): each unmerged path whose index
    stages are 1 and 2 (git's `UD`) or 1 and 3 (`DU`), read with `git ls-files --unmerged -z`.
    For each: which side deleted it (`UD`: this change, the commit being replayed; `DU`: the
    commit it is stacked on), the index stage holding the surviving text (`:2:` or `:3:`), the
    merge base and side for `git diff <base> HEAD|REBASE_HEAD -- <path>` (what the surviving side
    changed), the commit that deleted it, and the files that commit added or changed outside the
    change folders and the counter (`moved`), which is where its content may have gone.
- `plugins/factory/scripts/landing.py`
  - `cmd_resolve --continue`: skip the conflict-marker read for a conflicted path that is gone
    (a staged deletion); let `_stray()` also allow every `moved` path; stage the edited `moved`
    paths (`carried`) with the conflicted ones and name them in `runs/land-resolved`, so the
    review sees them.
  - `GREP_FOLLOWS_LONG`: name the threshold, `GREP_FOLLOWS_MIN = 3`, compared with the characters
    after `--` (nit 2026-11-20-9). Same behaviour.
- `plugins/factory/prompts/train-resolve.md`: a `## deleted` part (`PROMPT_PARTS` names it).
- `plugins/factory/agents/resolver.md`: the files it may edit include, for a modify/delete
  conflict, the ones the prompt names as where the content went; a deletion is a resolution.

The answer to the intent's open question: the script names the files the deleting commit added
or changed, and the resolver judges among them where the content went (a split is rarely a rename
git detects). Raised as a `[default]` decision.

## Work order

1. Evidence: the 189 report shape reads clean; a read that printed nothing before a later
   section's heading is still flagged.
2. Modify/delete in a train: a second change deletes a file the first edited and adds where it
   went; the stack reaches `resolve`, the prompt names the deletion, its sides and the moved file;
   the resolver keeps the deletion and edits the moved file; `--continue` goes through and the
   train lands. Also the other way round (`DU`): the first change deletes, the second edits.
3. The prompt fixture `train-resolve-deleted`.
4. The two nits.

## Tests

New tests go in new files or files 194's split leaves alone, so 194 doesn't conflict on them.

- `tests/test_evidence_headings.py`: 189's report shape owes no `exit:` (Outcome 1); the
  commands after it are still checked; a heading after an `exit:` ends the section; a read with
  no output before a later heading still owes one.
- `tests/test_train.py`: a modify/delete stack, either way round (`UD`, `DU`), reaches the
  resolver with the deletion named, `--continue` takes the deletion and the carried edit, and the
  train lands (Outcome 2); an edit outside the moved files is still refused.
- `tests/test_prompts.py`: `train-resolve-deleted`'s recorded prompt.
- `tests/test_decision_alternatives.py`: two decisions sharing one option are filed apart.

## Rollback

Nothing outside the repo: `git revert` undoes it all.
