DECISION: ESCALATE

**Why.** All four reviewers passed in round 1 and the gate is green (`./check.sh` exit 0, 3470 passed). Each outcome you can test has a test that fails without the change: 189's report shape, a modify/delete conflict in a train either way round (`UD` and `DU`), and both nits. Only the person can confirm D1, though: it widens which files an agent may edit, past the files the conflict names, and that check is in the sensitive `landing.py`. The security review also found one Medium problem in the same check, which you should look at before this lands.

**Open items**
- No CHANGE is open. Four nits are recorded in `findings.md`:
  - F1 (code): no test pins a read with output, then a blank line and `## Notes` with no `exit:`.
  - F2 (security, Medium): a gone `UU` file gets staged as a deletion.
  - F3 (security): the `read_evidence()` docstring overstates how strict the check is.
  - F4 (test): only one combined case covers the blank-line heading rule.

**Decisions to confirm**
- ESCALATED: D1: This is a policy call about what an agent may edit. `resolve --continue` would now accept the resolver's edits to every file the deleting commit added or changed, not just the conflicted ones. The security review notes this can include `[review] sensitive` paths such as `check.sh` or `.sdlc/config.toml`. The re-review and `runs/land-resolved` do still guard it. The plan and the default's WHY make a good case for it, but how far an agent's edits may reach is a rule only the person can approve.

**Other reasons I escalate**
- ESCALATED: look: `plugins/factory/scripts/landing.py: cmd_resolve --continue` (the `(root / f).is_file()` skip near line 2827) — security F2 (Medium). The check now accepts any conflicted path that is gone, not only a modify/delete one. A resolver that deletes a both-modified (`UU`) file gets that deletion staged without a word, where before the run stopped. The landing review and the marker still catch it, but this loosens a guard on a sensitive path. The suggested fix is to accept a missing file only when it is among `deleted_sides()`'s paths.

**For the person at ship**
- Look first at the `landing.py` diff: how `_stray()` now allows `moved` paths, how the `carried` files are staged and named in `runs/land-resolved`, and the missing-file skip (F2).
- Then look at `deleted_sides()` in `factory.py`: the `git ls-files --unmerged -z` read, and the `moved` set built from the deleting commit (change folders and the counter left out).
- Then look at the `read_evidence()` loop. The security review notes that a non-read command with no `exit:` can now find one in a later section if no blank line comes before the heading (F3).
- The intent's Affected section names three interfaces this changes, which you approved there: the `train-resolve` prompt's new `## deleted` part, the resolver's rule in `agents/resolver.md`, and the new `GREP_FOLLOWS_MIN`.
- Neither real-run outcome has been tried: the rerun of 189 and the landing of 194. Only tests that rebuild those cases have run.

- IMPACT: patch — two factory bugs are fixed (evidence that prints headings, and a modify/delete conflict in a train) plus two nits; nobody holding the previous release has to do anything differently.

**Undone items**
- UNDONE: The builder's `resolve` task (`agent --task resolve`, `prompts/resolve.md`) gets no `deleted` part: the landing loop only runs `train-resolve`, and the resolve prompt tells the builder to run no git command, which the deleted part's reads would contradict. `--continue` takes a modify/delete resolution from either. → dropped: not worth doing; the landing loop never runs the builder's `resolve` task, and `--continue` already accepts a modify/delete resolution from either task.
