---
id: 227
slug: docs-reviewer
kind: spec
created: 2026-11-22
updated: 2026-11-22
---

# 227 — A docs reviewer checks that a diff leaves no doc saying something false · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code:

- The factory's reviewers are `factory.py`'s `REVIEWERS`. The UI reviewers join a round on their own through `UI_REVIEWERS` and `ui_review()`, never through `reviewers`. `_depth_keys()` warns about them in a list, and `depth()`'s `beyond` leaves them out.
- `REVIEWERS` is copied as `scripts/factory_records.py`'s `REVIEWERS` (pinned in `tests/test_board.py:950`) and as `sdlc.py`'s `AGENT_ROLES` (pinned in `tests/test_findings.py:527`).
- Finding pass tags are `PASSES = ("correctness", "contract", "cost", "context")`. `Sdlc-Findings` counts them, and that trailer is a metrics contract: it can be extended, never redefined.
- Ship's further passes come from `_passes_report()`/`PASS_NAMES`, each with a `PASS_LINES` note line, a `SHIP_PASSES` `By:` value and a `SHIP_BRANCHES` side file.
- `[docs] context` is read today from the checkout (`_context_report()`). The factory reads its review lists from the base branch (`_review_list()`).
- `docs/FEATURES.md` is checked against the surface built from `CONFIG_KEYS` and the code by `tests/test_feature_map.py` (AGENTS.md, *Retrospectives*).

The requirements:

1. R1. A new factory reviewer `docs` exists: `plugins/factory/agents/reviewer-docs.md`, `model: sonnet`, with `Read, Grep, Glob, Bash` like `reviewer-code` and nothing that writes.
   - `docs` goes into `REVIEWERS`, `ROLES` and `SCALED`, so it runs on `sonnet` unless `factory.models.docs` sets another model.
   - `docs` also goes into the two copies, `factory_records.REVIEWERS` and `sdlc.AGENT_ROLES`. The existing pin tests fail if any one of the three is left out.
   - A test asserts `model_for("docs", cfg, …) == "sonnet"` with no `models` set.
2. R2. Each line the docs reviewer returns is `- CHANGE: [context] <doc>:<line>: what it says, what is now true, and the edit`. Its bar is the old Context pass's: only what the diff made false, or what a future reader needs and can't find, said nowhere else. Wording it could merely improve is at most a `- NIT:`.
   - `ROLE_PASS` gains `"docs": "context"`, so an untagged docs finding is still filed under `context`.
   - A test in `tests/test_factory_loop.py` asserts that `finding_pass("docs", "docs/a.md:3: x")` gives `("context", "docs/a.md:3: x")`.
3. R3. `docs` joins a round on its own, at either depth, as `ui` and `ux` do. It is never chosen through `reviewers` or `[light] reviewers`, and it never makes a run's depth full.
   - `_depth_keys()` warns `'docs' joins on its own, never in reviewers`.
   - `depth()`'s `beyond` leaves `docs` out.
   - Tests: a host list naming `docs` warns and drops it; a light run that ran `docs` stays light.
4. R4. The join rule is `docs_review(docs, rounds, changed, root)`, and it reads only files and paths. `docs` joins a round when any one of these holds:
   - (a) a changed path is itself a reviewed doc, or sits under a reviewed folder;
   - (b) a reviewed doc's text names a changed path, or its file name;
   - (c) a changed path has a `CLAUDE.md` or `AGENTS.md` above it, as `context` adds today;
   - (d) an earlier round of the run already ran `docs`;
   - (e) a changed path lies outside `tests/`.

   Changed paths come from `_changed_paths()`, so the change folder is left out. When `_rounds_at_depth()` sees it join, it adds `docs` to `run["reviewers"]`, and a round is `complete` only with a `docs` review.

   One test per clause. Clause (e)'s tests:
   - a diff touching only `src/a.py`, which no doc names, joins;
   - a diff touching only `tests/test_a.py`, which no doc names and which has no `CLAUDE.md`/`AGENTS.md` above it, doesn't join;
   - a diff touching only the change folder doesn't join.
5. R5. The docs it reads come from the base branch's `.sdlc/config.toml`, never the checkout, so a change can't take its own docs out of review. The list is `[docs] context`, plus a new `[docs] reviewed`.
   - Each `reviewed` entry ending in `/` names every file under that folder, as `risk_paths()` reads one. Any other entry is a glob.
   - With neither key set, the list is `CONFIG_KEYS`' `context` default, copied into `factory.py` and pinned to `sdlc.py`'s by a test.
   - Tests: a host with nothing set gets exactly today's default; a host with `reviewed = ["site/"]` gets `site/a.md`; editing the list in the checkout alone changes nothing.
6. R6. The reviewer's prompt names the docs it reads, and the stale lines. A stale line is a doc line naming a path the diff deletes or renames, worked out as `_context_report()`'s `stale` is. A test asserts that the prompt names exactly the listed docs and the stale lines.
7. R7. `reviewer-code.md` no longer has a Context pass. Its pass 5 is gone, and its tag list in *What you return* no longer offers `[context]`. With this, the two never raise the same line.
   - A test reads the agent file and fails if `**Context.**` or `[docs] context` appears in it.
8. R8. `max_runs()` counts `docs` in every round, as it counts the UI reviewers, since any round's diff can meet R4. The existing `max_runs` test is updated to the new bound.
9. R9. `/sdlc:ship`, for a change built by hand, gets the same pass from a new core agent `agents/docs.md` (`sdlc:docs`) with `tools: Read, Grep, Glob`.
   - `docs` joins `PASS_NAMES` and `_passes_report()`. It applies by R4's clauses (a), (b), (c) and (e) over the base branch's list (R5). Ship has no rounds, so (d) doesn't apply. It never applies on a factory run (`decision.md`).
   - It has a note line `Docs review: ran|skipped` (`DOCS_RE` in `PASS_LINES`), a `PASS_OF`/`PASS_SAID` entry, `By: ship-docs` in `SHIP_PASSES`, and the side file `skills/ship/docs.md`, which `SHIP_BRANCHES` names when it applies.
   - Tests in `tests/test_preflight*.py`/`tests/test_findings.py`: it applies on a diff touching `src/a.py`; it doesn't on a diff touching only `tests/test_a.py` that no doc names; ship's question says `without the docs review (<why>)` when the note says skipped.
10. R10. When `docs` applies at ship, ship's own Context pass leaves "does it now say something false" to the agent, and keeps the "a future session needs it" and "already said elsewhere, so a pointer" questions. When it doesn't apply, the Context pass asks all three, as today.
    - `skills/ship/SKILL.md` Step 3 says this.
    - A test asserts that Step 3 names `docs.md`.
    - `tests/test_skills.py`'s existing rules cover the side file (named in `SKILL.md`, no frontmatter, WAIT or commit).
11. R11. A host whose factory `reviewers` (or `[light] reviewers`) names only `code` still has its docs checked after upgrading, because `docs` joins under R4 whatever those lists say. A test sets `reviewers = ["code"]` and a diff touching `src/a.py`, and asserts that `docs` is in the round's expected reviewers.
12. R12. Each doc edit is pinned by a test, so none is a look for the person:
    1. **`guide/review.md`.** Its **context** row reads `Factory: reviewer-docs, when the diff calls it in` and names `sdlc:docs` for ship. A test in `tests/test_defaults.py` asserts that the row's text contains `reviewer-docs` and `sdlc:docs`, and doesn't contain `reviewer-code`'s context pass.
    2. **`docs/REFERENCE.md`.** It names `docs.reviewed` in *The docs*, and its `[docs]` config example shows a `reviewed` line. A test asserts every `CONFIG_KEYS["docs"]` key appears in REFERENCE.md as `docs.<key>`. Today's keys already do, so the new test fails only on a missing `reviewed`.
    3. **`plugins/factory/README.md`.** Its reviewer table has a row for `docs`, naming `reviewer-docs`, `sonnet` and `joins on its own`. A test asserts every role in `REVIEWERS` has a row in that table, and that the `docs` row holds those three phrases.
    4. **`docs/FEATURES.md`.** It has an entry for `docs.reviewed` and one for the ship pass `sdlc:docs`. `tests/test_feature_map.py` fails without the key's entry, since it maps `CONFIG_KEYS`. A new assertion there fails without the pass's entry, by checking each `PASS_NAMES` name appears.
    5. **The build skill.** `plugins/factory/skills/build/SKILL.md`'s reviewers sentence (now line 82) gains `` `docs`, which joins on its own `` beside its words on `ui` and `ux`. A test asserts the file holds that phrase.
    6. **AGENTS.md.** Its Ship paragraph reads `four more core agents, sdlc:security, sdlc:docs, sdlc:ui and sdlc:ux`. A test asserts that every `agents/*.md` stem appears in AGENTS.md as `sdlc:<stem>`. `reviewer` and `insight` already do, so the test fails only on a missing `docs`.

    Because `guide/` changes, `sdlc.py record` runs from this checkout, and the gate's drift check passes.

## Design

**Factory side (`factory.py`).**

- `docs` is added to `REVIEWERS`, `ROLES` and `SCALED`.
- A new `JOINING = UI_REVIEWERS + ("docs",)` replaces `UI_REVIEWERS` where the code means "never chosen, joins on its own". These are `_depth_keys()`' `chosen` and its warning, and `depth()`'s `beyond`. `UI_REVIEWERS` stays where it means the page: `shots`, `ui_review()`, `max_runs`' UI count and `agent`'s screenshot branch at 5470.
- A new `_docs_at(root, base)` reads the base branch's `[docs]` through `git show`, the way `_review_list()` does. It returns the `context` list (else `CONTEXT_DEFAULT`, the pinned copy) and the `reviewed` list.
- A new `reviewed_docs(root, base)` expands that list to the files that exist: folders and globs, against `git ls-files`.
- `docs_review()` applies R4's five clauses in order and returns at the first that holds. Clause (e) is a prefix test on `tests/`, over paths that already leave out the change folder.
- `_rounds_at_depth()` sets `run["docs"]` and adds the role, as it does for `ui`.
- The reviewer's prompt is built where the other reviewers' are (`agent --task review --role docs`). It lists the docs and the stale lines. The stale lines are worked out in `factory.py`, never by importing `sdlc.py`, from the same `--name-status -M` reading `changed_paths()` uses.
- Landing rounds take their roles from the same `_rounds_at_depth()`, so a landing round gets `docs` by the same rule.

**`reviewer-docs.md`.** It has the same frame as `reviewer-code.md`: given the change folder, the round and the diff; never runs the gate; same later-rounds rules and same return format. It has one pass, the old Context pass, widened from "the docs a session reads" to every listed doc, with the bar R2 states. Wording only is a `- NIT:` with weights. The pass doesn't check whether a doc repeats what the code or another doc says (see the open questions below). The one exception is the context docs, where the old pass already proposed a pointer instead of a repeat, and it keeps that.

**Core side (`sdlc.py`).**

- `CONFIG_KEYS["docs"]["reviewed"] = []`, with a comment.
- `_passes_report()` gains `docs`. It uses `_docs_at`'s core twin, `_docs_list_at(home, trunk)`, which reads the base branch's config as `_ui_at()` does, plus the changed paths it already computes and the clauses R9 names.
- `_context_report()` is unchanged: it still gives ship's own Context pass its list and `stale` lines.
- `PASS_NAMES`, `PASS_OF`, `PASS_SAID`, `PASS_LINES`, `SHIP_PASSES` and `SHIP_BRANCHES` each gain their `docs` entry.
- `AGENT_ROLES` gains `docs`, so `By: docs` from a factory run counts as an agent's finding and `By: ship-docs` as ship's.

**Edge cases.**

- No listed doc exists: `docs` still joins by (c), (d) or (e).
- A doc deleted by the diff: (a) holds and the stale lines name it.
- A rework round that touches only `tests/`: `docs` keeps running by (d) if it ran before. That matches `ui_review()`'s `ran`.
- A host whose tests live outside `tests/`: those paths meet (e), so `docs` joins more often, never less. That is the safe direction.

## Contracts touched

- **Agents that judge have no Write** (Architecture, the factory). `reviewer-docs` has Read, Grep, Glob and Bash, like `reviewer-code`. `sdlc:docs` has Read, Grep and Glob, as every core agent does.
- **Mechanism vs judgment.** The script decides when the reviewer joins and lists the docs and the stale lines. The agent only judges what is false.
- **Mechanism vs policy.** The plugin knows nothing of a host's layout, and clause (e)'s `tests/` is a literal. A host with no `tests/` folder gets `docs` on every diff outside its change folder. That keeps the check and never drops it, so nothing about a host is assumed that could lose a review.
- **Copies pinned by tests.** `REVIEWERS` has three copies (`factory.py`, `factory_records.py`, `sdlc.AGENT_ROLES`), and the context default gets one new copy. Each is pinned, and `factory.py` still never imports `sdlc.py`.
- **A finding counted for the wrong reviewer** (REVIEW.md). `By: docs` is an agent role and `By: ship-docs` is ship's, kept apart by the same prefix rule. `test_finding_by_names_every_factory_reviewer` covers it once `AGENT_ROLES` has `docs`.
- **Metrics trailers are a contract** (`scripts/metrics.py`). No new pass tag: docs findings take `context`, so `Sdlc-Findings` keeps its keys.
- **A change to what something a host already has means.**
  - A host's `reviewers` keeps its meaning. `docs` joins outside it, and naming it there warns as `ui` does, rather than failing.
  - `[docs] context` keeps its meaning (what gives a session its context). `reviewed` is new and empty by default.
  - `code` no longer checks docs. `docs` checks them on every diff that touches anything outside `tests/` and the change folder, so such a diff keeps the check it had. A diff touching only `tests/` keeps it whenever a doc names a changed path, or a `CLAUDE.md`/`AGENTS.md` sits above one.
- **Read from the base branch** (Ship, the factory). The docs list is read like `[review] sensitive` and `[ui]`, so a change can't take its own docs out of review.
- **Skills** (`tests/test_skills.py`). `skills/ship/docs.md` is a side file: named in `SKILL.md`, no frontmatter, WAIT or commit. It runs no command, so no new `Bash(...)` rule.
- **This repo's process docs hold only its answers.** The guide's context row is edited in `guide/`, never mirrored into `.sdlc/REVIEW.md`. Then `sdlc.py record`.

No invariant needs to change.

## Alternatives rejected

- **Keep the Context pass in `reviewer-code` and add `docs` beside it.** Two reviewers would raise the same line, and the arbiter would weigh duplicates. The intent asks that they never overlap.
- **A new `[docs]` pass tag.** It would add a key to `Sdlc-Findings` and to findings.md's pass vocabulary across the board, retro and metrics. `context` already means "a doc no longer tells the truth".
- **Put `docs` in the default `reviewers` lists.** A host that set its own list (say `["code"]`) would silently lose its docs review on upgrade, which the intent rules out.
- **One list (`[docs] context`) for every doc.** `context` drives ship's own Context pass, whose bar is "what a session needs". A docs site in it would make ship weigh every user page as session context, and propose pointers there. The code reads `context` as session context (`CONFIG_KEYS`' comment, `_context_report()`).
- **Join only by clauses (a)–(d).** A diff that changes what a function does, in a file no doc names by path or file name, would lose the check `code`'s Context pass gave it. Clause (e) closes that gap.
- **Join on every diff, `tests/` included.** That costs a sonnet run on rounds that touch only tests, which no doc names and which no `CLAUDE.md` sits above. Those are the rounds that can't make a doc false, which the intent's cost constraint leaves out.
- **A host list of the paths that call it in (in the style of `[ui] paths`).** A host has to keep that list up to date, and an unset list would have to mean "every path" anyway.
- **Read the list through `sdlc.py config`.** `factory.py` never imports `sdlc.py`, and the other base-branch lists are read in place.

## Verification

```bash
./check.sh
uv run --group dev pytest -q -n auto tests/test_factory_loop.py tests/test_findings.py tests/test_board.py tests/test_skills.py tests/test_feature_map.py tests/test_defaults.py
uv run --quiet --script scripts/sdlc.py drift
grep -n '\*\*Context\.\*\*\|\[docs\] context' plugins/factory/agents/reviewer-code.md
grep -n 'reviewer-docs' guide/review.md plugins/factory/README.md
grep -n 'docs\.reviewed' docs/REFERENCE.md docs/FEATURES.md
grep -n 'sdlc:docs' AGENTS.md docs/FEATURES.md guide/review.md
grep -n '`docs`, which joins on its own' plugins/factory/skills/build/SKILL.md
```

What healthy looks like:

- `check.sh` ends green: ruff clean, pytest passing with the new tests counted, and `claude plugin validate --strict` passing.
- `drift` reports nothing.
- The first grep prints nothing. Every other grep prints at least one line in each file it names.
- In a scratch run, `factory.py start`/`status` shows `docs` among a round's expected reviewers on a diff touching `scripts/sdlc.py`. It is absent on a diff touching only `tests/test_a.py`, which no doc names.
- `sdlc.py preflight <NNN>` shows `passes.docs.applies: true`, and `branches` includes `docs.md`, on the first diff and not on the second.

