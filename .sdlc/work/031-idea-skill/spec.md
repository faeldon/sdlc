---
id: 031
slug: idea-skill
kind: spec
created: 2026-10-27
updated: 2026-10-27
---

# 031 — An /sdlc:idea skill, and inbox-commit for every kind of entry · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1.** `sdlc.py inbox-commit` replaces `bug-commit`, with no shim. From the main checkout it
   behaves exactly as `bug-commit` does today: one commit of the register alone on `git.base`,
   `File`/`Update`/`Retire <id>`, plus `--triaged`/`--why`. `bug-commit` is gone from the parser
   and the module docstring. Tests: every `test_bugs.py`/`test_archive.py` case runs under the new
   name, and `bug-commit` exits with argparse's invalid choice.
2. **R2.** Retire reasons depend on the entry's kind:
   - an idea (`[idea]`, `[seed]` or any other tag) takes `duplicate`, `superseded` or `declined`;
   - a `[bug]` takes `duplicate`, `not-a-bug`, `wontfix` or `cant-reproduce`;
   - a `[nit]` can't be removed here, and the refusal says ship retires nits;
   - a reason that doesn't fit the kind is refused, naming the reasons that do.

   Tests: one per kind, plus a mismatched reason.
3. **R3.** Retiring a `[building]` entry is refused: the change building it removes it at ship, or
   `/sdlc:drop` records why not. Test.
4. **R4.** `Sdlc-Retired:` stays a bug-only trailer, so `bugs_retro()` keeps counting only bugs.
   Retiring an idea records its reason only in the subject's body, as `Reason <id>: <word>`. Test:
   an idea's `Retire` commit carries no `Sdlc-Retired:` line.
5. **R5.** Run from a change's worktree, `inbox-commit <id>…` files the named entries on `main`, in
   the main checkout's register:
   - an id that's new in the worktree's register is appended;
   - one that changed replaces its entry;
   - one that's missing is removed, with its `--reason`.

   It commits that one file on the main checkout's `git.base`, then puts the worktree's register
   back to its own `HEAD` for those ids alone, keeping every other uncommitted edit. The worktree
   picks the entries up when it next comes up to date (`cmd_base`). Without ids in a worktree, it
   refuses. Tests: a new idea filed from a worktree lands on `main`, and the worktree's own
   `[building]` edit survives untouched; an id the worktree didn't change is refused.
6. **R6.** From a worktree, it refuses before writing anything when:
   - the main checkout isn't on `git.base`;
   - the main checkout has anything uncommitted, register included, since that could be another
     session's unfinished draft;
   - the id isn't in the worktree's register, or a new id is already in `main`'s.

   Tests for the first two.
7. **R7.** `inbox-commit` holds the same `flock` on the main checkout's `.sdlc/` that `claim()`
   takes, from reading `main`'s register to the commit, so two sessions filing at once can't lose
   either's entry. Test: a held lock makes it wait or refuse, matching `claim()`'s behaviour.
8. **R8.** A new `skills/idea/SKILL.md`, `/sdlc:idea`:
   - **Filing:** it takes an idea in the person's words, checks the register for one that already
     covers it, takes an id from `next-entry`, and drafts `## [<id>] [idea] <title>` with prose
     that names no host, an `After: <id>` line when it follows another seed, and `Raised <date>.`
   - **Editing or retiring** an existing idea goes through the same skill. Retiring uses R2's
     reasons. An entry that is really a bug is sent to `/sdlc:bug`.
   - **The commit:** after one WAIT it edits the register in its own checkout and runs
     `inbox-commit`, with the id when it's in a worktree.
   - **`allowed-tools`:** Read, Write, Edit, and `config`, `next-entry` and `inbox-commit` rules
     only.

   It passes every `test_skills.py` invariant, and its description says to use `/sdlc:bug` for
   something broken.
9. **R9.** `/sdlc:bug` files, retires and retags from any checkout. The main-checkout stop goes;
   in a worktree it passes the id to `inbox-commit`. Its `allowed-tools` rule and command become
   `inbox-commit`. `/sdlc:triage` takes the renamed rule and command and nothing else, and stays
   main-only.
10. **R10.** AGENTS.md (the bugs and intake paragraphs, and the list of writing skills),
    `docs/REFERENCE.md` and README.md's skill table name `inbox-commit` and `/sdlc:idea`, and say
    that filing works from a worktree onto `main`.
11. **R11.** `./check.sh` passes.

## Design

**Kinds.** `RETIRE_REASONS` becomes a dict keyed by kind: `idea`, `bug`, `nit` (empty). The kind
comes from the existing `is_bug()`/`is_nit()` on the removed entry, and anything else is an idea.
Reason checking moves from the argument loop into the removal loop, where the entry is known.
`BUG_SUBJECTS` is renamed `INBOX_SUBJECTS`.

**One function, two places to run it from.** `cmd_inbox_commit(root, ids, reasons, triaged, whys)`
keeps today's path when `root` is the main checkout. In a worktree it takes the lock, checks R6,
and builds `main`'s new register text entry by entry with `parse_entries()`: append, replace or
remove. It writes that text, commits as today, then rewrites the worktree's register with those
ids restored to the worktree's `HEAD` text. Both rewrites splice whole entries, from a heading to
the line before the next `## `, the same span `/sdlc:bug` deletes. Subject, body and trailers come
from the same code on both paths. If the commit fails, `main`'s register is put back before it
reports.

**Why `main` and not the change's branch.** An entry committed on the change's branch is invisible
until close and lost on drop, since the `Drop` merge keeps `main`'s tree (`-s ours`). Filing on
`main` makes it visible at once to `status` everywhere. The worktree gets it through the rebase
that ship's Step 0 already does.

**The skill** reads like `/sdlc:bug`: Step 0 runs `config`, and the session's own `work.register`
is the file it edits. It never writes outside its checkout; the script does that.

## Contracts touched

- **AGENTS.md: "`bug-commit` is the only code that commits the inbox, from the main checkout
  alone."** This changes. The policy text becomes: `inbox-commit` is the only code that commits the
  inbox, always on `main` in the main checkout, and it can be run from a change's worktree for the
  entries it names. R10 edits it in this change.
- **A skill's WAIT and `allowed-tools` (always Tier 2).** There's a new writing skill with one
  WAIT, and the rule in two skills is renamed. `idea` joins the writing-skills list in AGENTS.md
  and the test.
- **Narrow `allowed-tools` / logic in the script.** The worktree branch, the splicing and the lock
  are all in `sdlc.py`. The skills' bash stays as plain commands.
- **Only publish pushes.** `inbox-commit` commits and never pushes.
- **Nothing local.** The skill tells the writer to name no host, as `/sdlc:bug` does. Test data
  stays neutral.
- **Register format and ids.** No change. Ids still come from `next-entry`, which already counts
  every checkout's uncommitted register.
- **Shims.** None, by decision. `bug-commit` shipped in 1.2.0, but nothing setup writes names it.

## Alternatives rejected

- **A shim for `bug-commit`:** declined, since nothing setup writes names the command.
- **Committing the entry on the change's branch:** the entry would be hidden until close and lost
  on drop.
- **The skill editing the main checkout's register directly:** that writes outside the session's
  worktree, which isolation can refuse, and it leaves the read-modify-write unlocked.
- **Carrying every uncommitted register edit from the worktree, with no ids:** that would sweep the
  change's own `[building]` tag and nits onto `main`.
- **One filing skill for both kinds:** two were chosen. Each keeps one WAIT and an interview that
  fits its kind.
- **Reading old `Seed <id>:` commits:** nothing reads `File`/`Update`/`Retire` subjects, only
  `Sdlc-Retired:` trailers. `next_entry_ids()` already reads every commit that held the register.

## Verification

- `uv run --group dev pytest tests/test_bugs.py tests/test_archive.py tests/test_skills.py
  tests/test_adoption.py -q`, then `./check.sh`. All green.
- By hand, from a scratch change's worktree: `/sdlc:idea` files an entry. `git log -1 main` shows
  `File <id>` touching only the register, `status` in both checkouts lists the entry, and the
  worktree's `git diff` no longer shows it.
