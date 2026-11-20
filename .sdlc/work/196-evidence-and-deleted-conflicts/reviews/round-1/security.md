I've finished reading the diff and the fence logic, and found nothing Critical or High, so the verdict is PASS. The full review follows.

VERDICT: PASS

## Notes

**Trust boundaries the diff touches**

1. **The resolver's output** (a model) against the `resolve --continue` fence (`_stray()`). The fence now also allows `moved`: the files the deleting commit added or changed.
2. **The builder's reply** (a model) against the `## Evidence` parser (`read_evidence()`).
3. **Paths from the repo's own commits**, which are written into the resolver's prompt (`deleted` part).

**STRIDE on the widened fence (Tampering, Elevation)**

- **The script decides the allowed set, not the model.** `deleted_sides()` builds it from `git ls-files --unmerged` and `git diff-tree --diff-filter=AM` on the deleting commit. Change folders and `COUNTER` are left out, and only files still in the tree count. The resolver can't widen the set by anything it writes. At `--continue` the unmerged stages are still in the index (the resolver runs no git that writes), so the set is computed again the same way.
- **The deleting commit is one the train already holds.** It was built, reviewed and approved on its own, so the resolver may only edit files that change already touched. If one of them is a `[review] sensitive` path (`check.sh`, `.sdlc/config.toml`), the resolver may now edit it.
- **The re-review still applies.** `carried` paths are written into `runs/land-resolved`, and `resolution_signals()` raises `LANDING_RESOLVED` until the landing review of that round passes. The self-approving WAIT can't skip a resolution the review hasn't seen. This keeps the intent's constraint that a resolved conflict is reviewed again.
- **Deleting a file outside `moved` is still refused.** A deleted tracked file shows a worktree column that isn't blank, so `_stray()` flags it. That errs towards refusing.

**Medium: a both-modified conflict can now become a deletion.** In `landing.py:2827`, `(root / f).is_file()` skips the marker read for any conflicted path that is gone, not only a modify/delete one. A resolver that deletes a `UU` file now gets that deletion staged without a word, where before the run crashed. The landing review still has to pass it, and the marker names it, so it isn't exploitable past review.
- Fix: allow a missing file only when `f` is among `deleted_sides()`'s paths. Refuse any other missing conflicted path as "a conflicted file was deleted".

**Low: the evidence check is looser in one case.** In `factory.py:1586`, after a command that isn't a read and has no `exit:`, a `## ` line with no blank line before it no longer ends the section. The command can then find an `exit:` in a later section. The docstring says this never happens, but it only holds when a blank line comes before the heading. Evidence is the model's own report, not a security control, so this is a correctness and robustness point.
- Fix: say so in the docstring, or end the section at a `## ` line whenever the open command isn't a read that has printed.

**Low and Info**
- Paths and the `moved` list are put into the resolver's prompt as they are. They come from commits the train already holds, so this is not a new injection vector.
- `moved` entries are kept only if `is_file()`, which follows symlinks. The resolver's `Edit` already reaches anything, and the fence is a check after the fact, so a symlink adds no new exposure.

- NIT: plugins/factory/scripts/landing.py:2827: restrict the missing-file pass to `deleted_sides()` paths so a `UU` file can't silently become a staged deletion {robustness S med}
- NIT: plugins/factory/scripts/factory.py:1569: the docstring says a command that owes its `exit:` "never finds it in a later section", but a heading with no blank line before it doesn't end the section {docs S low}

**Done well**
- The fence stays decided by the script (D1's WHY), which keeps the boundary out of the prompt.
- `carried` is named in the marker for the review.
- The `by_alts` tightening is a small integrity gain: one shared option can no longer merge two different decisions.
- The `GREP_FOLLOWS_MIN` rewrite behaves the same as before (`len(name) - 2 >= 3` is the old `len(name) >= 5`), so the grep symlink refusal still holds.

**What I checked**
- `intent.md`, `plan.md`, `decisions.md` (D1 is open, and I agree with its default) and the full `git diff`.
- `_stray()`, `_amend_record()`, `resolution_signals()`, and the resolver agent's tools and rules.
- The gate record `build/round-1.gate.md` is PASS. I ran no gate or tests myself.
