# Notes

> What happened while this change was built that its intent, spec and plan don't say. Free-form,
> with one rule: anything left undone is an unticked `- [ ]` line. `/sdlc:ship` gives each one a
> disposition, carried to a `.sdlc/work/inbox.md` seed or dropped with a reason, and `sdlc.py ship`
> refuses while one is still unticked.

## Size (R3)

| File | Lines | Bytes |
|---|---|---|
| `skills/ship/SKILL.md` on `main` (after 055) | 550 | 36,275 |
| `skills/ship/SKILL.md` now | 475 | 30,203 |
| `factory.md` | 27 | 1,719 |
| `undone.md` | 28 | 1,422 |
| `cases.md` | 23 | 1,404 |
| `fresh.md` | 20 | 1,357 |
| `closes.md` | 21 | 1,208 |
| `recover.md` | 13 | 684 |

A plain ship run reads 6,072 bytes (17%, about 1,520 tokens) less than before. A run that needs
every branch reads about 1,700 bytes more, for the files' titles and the pointer lines.

## Rebased onto 054 and 055

`base` refused while the work was uncommitted, since 054 and 055 changed six of the same files. A
WIP commit rebased onto `main` with one conflict, `AGENTS.md`'s skills invariant, which now holds
both 055's dialog sentence and this change's side-file sentence. 055's seven lines in ship's Step
5 took `SKILL.md` to 479, so Step 0's `branches` entry and its read instruction were tightened, and
Step 4's "Issues it closes" pointer joined the other three, back to 475. The WIP commit was then
undone (`git reset --soft main`), so the change lands as one commit.

## Departures from the plan

- `undone.md`'s Step 4 gained one sentence ("Each carried seed takes an id from Step 4's
  `next-entry` call"), so the file stands on its own; the `Ids` paragraph that says so stays in
  `SKILL.md`.
- `_steps()` in `tests/test_skills.py` now reads a branch file too, and splits a heading's number
  on any whitespace, since a branch file's `## Step N` heading has no title after it.
- Three more tests over every skill read its side files with it: only the named steps push, only
  close and drop leave the worktree, and no shipped text names `migrate-inbox`.
