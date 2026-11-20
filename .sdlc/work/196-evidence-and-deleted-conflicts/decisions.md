# Decisions

- [x] D1 (builder round 1, default): How does the resolver say where a deleted file's content went? (the intent's open question) Going ahead with this: the script lists the files the deleting commit added or changed, the resolver picks among them, and only those files pass `--continue` beyond the conflict's own. → decided: the assumed default, confirmed
  - OPTION: the deleting commit's added or changed files, resolver's judgment — handles a split like 194's, and the edits stay fenced and are re-reviewed; the resolver may touch more files than the conflict lists
  - OPTION: only a rename git detects — tighter; a split is rarely detected, so 194 still couldn't land unattended
  - OPTION: the resolver names the destination in its reply — most flexible; the script can't check prose, which breaks the rule that the script decides what may change
  - WHY: the intent's outcome needs 194 to land unattended, and the constraint needs the script to decide which files may change.
- [x] D2 (approver round 1, look): `plugins/factory/scripts/landing.py: cmd_resolve --continue` (the `(root / f).is_file()` skip near line 2827) — security F2 (Medium). The check now accepts any conflicted path that is gone, not only a modify/delete one. A resolver that deletes a both-modified (`UU`) file gets that deletion staged without a word, where before the run stopped. The landing review and the marker still catch it, but this loosens a guard on a sensitive path. The suggested fix is to accept a missing file only when it is among `deleted_sides()`'s paths. → decided: seen
