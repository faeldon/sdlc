# 185-landing-gates — entries

Retire 2026-11-19-36: taken in by 185-landing-gates
Retire 2026-11-19-47: taken in by 185-landing-gates
Retire 2026-11-19-48: taken in by 185-landing-gates

## [2026-11-19-68] [idea] Land skill description names the build at the tip and the approver's check judgement

Left undone by 185-landing-gates, carried forward when it landed: The land skill's frontmatter `description` still lists what a landing runs without the build at the tip or the approver's judgement of changed checks; Step 3 and the steps list say both. A wording pass on the description alone, kept out of this change.
See .sdlc/work/185-landing-gates/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-69] [idea] Landing records that an agent in the change's folder can't forge

Left undone by 185-landing-gates, carried forward when it landed: pre-existing: plugins/factory/scripts/landing.py:2180: gate/build/accept records are trusted by the hash they state, which any agent that can write in the change's folder can write; a script-side signature or a record kept outside the tree would close it
See .sdlc/work/185-landing-gates/notes.md in its commit.
Raised 2026-11-19.

## [2026-11-19-70] [nit] the edited factory paragraph has two lines over the file's ~100-column wrap (`change calls for it (build_due()).

Raised by the code review of 185-landing-gates, round 1: AGENTS.md:263: the edited factory paragraph has two lines over the file's ~100-column wrap (`change calls for it (build_due()). Landing, in …`, and `approver and the read-only list together, …`). Re-wrap them.

Theme: docs
Paths: AGENTS.md
Cost: S
Value: low
Raised by: 185-landing-gates (correctness)

## [2026-11-19-71] [nit] `_train_begin` calls `_preflight` once per change at begin, as the spec says.

Raised by the code review of 185-landing-gates, round 1: plugins/factory/scripts/landing.py:1900: `_train_begin` calls `_preflight` once per change at begin, as the spec says. Where preflight can't be read, it records `checks: []` with a hash. This is safe, since every check then counts as changed, but a one-line comment saying so would help.

Theme: docs
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 185-landing-gates (correctness)

## [2026-11-19-72] [nit] the docstring says a symlink out is refused "for a word naming an existing path"; say that a program walking the tree itself is not covered

Raised by the security review of 185-landing-gates, round 1: plugins/factory/scripts/landing.py:842: the docstring says a symlink out is refused "for a word naming an existing path"; say that a program walking the tree itself is not covered

Theme: docs
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: low
Raised by: 185-landing-gates (contract)

## [2026-11-19-73] [nit] the R9 test drives a real train to `accept` and then edits `checks.md`.

Raised by the test review of 185-landing-gates, round 1: tests/test_train.py:2307: the R9 test drives a real train to `accept` and then edits `checks.md`. The edited command is `rm -f bb.txt`, which is off the list, so it never exercises the case where an edit passes R5 but loses the approver's clearance.

Theme: tests
Paths: tests/test_train.py
Cost: S
Value: low
Raised by: 185-landing-gates (correctness)

## [2026-11-19-74] [nit] GNU grep accepts unambiguous long-option prefixes, so `--der`/`--dereference` passes the exact `GREP_FOLLOWS_LONG` match and still follows symlinks while recursing; refuse any `--` word that is a prefix of `--dereference-recursive` (length ≥ 3), or refuse every grep long option not on a short allow-list

Raised by the security review of 185-landing-gates, round 2: plugins/factory/scripts/landing.py:876: GNU grep accepts unambiguous long-option prefixes, so `--der`/`--dereference` passes the exact `GREP_FOLLOWS_LONG` match and still follows symlinks while recursing; refuse any `--` word that is a prefix of `--dereference-recursive` (length ≥ 3), or refuse every grep long option not on a short allow-list

Theme: robustness
Paths: plugins/factory/scripts/landing.py
Cost: S
Value: med
Raised by: 185-landing-gates (contract)
