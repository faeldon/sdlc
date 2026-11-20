
**What I settled, and what's still yours**

- **Resolved: should the guard be one function shared with `land`'s commit?** No, it lives only in
  `--continue`. `land` commits through `sdlc`'s `ship` with no rebase and no `REBASE_HEAD`, and
  `_amend_record()` (`landing.py:1405`) already holds its amend to the change's folder. DIRECTION.md
  M20's "and the landing's commits" stays for the change that takes 2026-11-19-69.
- **Resolved: does a resolver ever need to stage a path `REBASE_HEAD` doesn't touch?** No. The
  resolver runs only git reads (`agents/resolver.md`). The script stages `.sdlc/last-id` only when it
  conflicted (`_settle_counter()`, `landing.py:2680`), and that means `REBASE_HEAD` owns it. The
  resolve run's own records are already allowed by name (`RESOLVE_RECORDS`, the marker,
  `build/land-<n>.md`). The one exception is the DU case: there the moved files sit on `HEAD`'s
  side, so they stay allowed through `deleted_sides()`'s `moved`.
- **Left for you: the path-level limit.** A resolver could stage a different text for a path
  `REBASE_HEAD` owns but that didn't conflict, and it would still pass. Accepting it as it stands
  means the review and the tip's gate are the only check. Filing it as a bug or seed means a later
  change checks the staged text against a `git merge-tree` replay of that path, which costs one
  merge per owned path on every `--continue`.
- **Left for you: the review bullet's wording.** I kept it exactly as seed 2026-11-20-40 words it,
  as the intent asks. Other Pass 1 bullets end with a sentence naming the tests that pin them. If
  you want one here, it would name the new
  `test_a_staged_path_the_replayed_commit_doesnt_own_is_refused` and
  `test_a_staged_modify_delete_resolution_lands`.
- **Not taken in: nit 2026-11-20-29** (nothing tests the guard that a path staged as kept isn't
  counted as a deletion). It's close to this work, but the intent doesn't name it, so it is not on
  the `Nits taken in:` line.
