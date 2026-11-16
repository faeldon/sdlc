---
id: 058
slug: setup-stops-when-complete
kind: plan
created: 2026-11-16
updated: 2026-11-16
---

# 058 — Setup stops on a set-up repo before reading its first-setup steps · plan

## Context

Every `/sdlc:setup` run reads all 314 lines of `skills/setup/SKILL.md`, including reruns on a repo
that is already set up, which need none of Steps 1–3. Its prose rule for stopping ("every item
`ok`") never holds on a repo that leaves `commands.build`/`scan` unset by choice, this one
included. The approved spec (`spec.md`, R1–R14) adds `complete` and `unset` to `readiness`, moves
Step 0's drift explanation, the `reset` text and Steps 1–3 into `skills/setup/drafts.md`, read
only when setup isn't stopping, and proves the stop with a new `setup` eval case on a set-up
fixture.

## Files to change

- **`scripts/sdlc.py`** — `cmd_readiness()`:
  - `UNSET_IS_A_CHOICE = ("commands.build", "commands.scan")` beside it.
  - Hoist `found = drift(root)` (computed now only inside the `drift` item's `else`; `None` with
    no config).
  - `unset` = those items `missing`; `complete` = config file exists, every item `ok`/`n/a` or in
    `unset`, and `found`'s `breaking`, `refresh`, `report` all empty.
  - Both into `out` right after `ready`; docstring says what `complete` means. Nothing else moves.
- **`skills/setup/SKILL.md`**: keep frontmatter, intro, Step 0's bash and a short reading of the
  three outputs, then the branch (R5): `complete` true and no argument → say set up, list `unset`,
  stop; otherwise `Read` `${CLAUDE_PLUGIN_ROOT}/skills/setup/drafts.md` now, then go on from its
  Step 1. Pointer lines where Steps 1–3 were. Keep Step 4 (WAIT, text unchanged), 5, 6, Out of
  scope. Target ≤ 150 lines.
- **`skills/setup/drafts.md`** (new): a title and a sentence on when it's read; the drift lists
  explanation and the `product`/`project`/`reset` paragraphs, then `## Step 1`, `## Step 2`,
  `## Step 3` moved verbatim. R8: Step 1 also names CI workflow files (`.github/workflows/`) and
  release and install scripts.
- **`evals/scaffold.sh`**: a fixture with a `main` file (no `branch`) copies `change/` onto `main`,
  commits, runs `sdlc.py record`, commits `.sdlc/setup.json`, exits.
- **`evals/fixtures/set-up/`** (new): `main` file; `change/` with `.sdlc/config.toml`, filled
  `.sdlc/SDLC.md` and `.sdlc/REVIEW.md`, `AGENTS.md`, `.claude/settings.json` (all of
  `ALLOW_RULES` + `ATTRIBUTION_OFF`). No `CLAUDE.md`. Neutral content.
- **`evals/setup/`** (new): `case.yaml` (`tags: [setup]`), `scaffold.sh`, `prompt.md`, graders
  `asks-config`, `never-writes`, `never-edits`, `never-commits`, `never-pushes`,
  `never-reads-drafts`, `says-set-up`.
- **Tests**: `tests/test_readiness.py` (complete and each false case, `unset`);
  `tests/test_evals.py` (fixtures with `main`, the fixture is complete, the setup case's graders,
  `never-reads-drafts` hit/miss); `tests/test_skills.py` (budget ≤150, Step 0 names `complete`,
  `unset` and the side file, WAIT text pinned, R8); `tests/test_retro.py` (setup's `branches`);
  `tests/test_archive.py` (`skills/setup/drafts.md` reach).
- **Docs**: `AGENTS.md`, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md`.
- **`notes.md`**: final line counts, departures.

## Work order

1. Script `complete`/`unset`; set-up fixture + scaffold mode; readiness tests.
2. Split the skill into `drafts.md`; R8; skill/retro/archive tests.
3. Eval case + grader tests.
4. Docs, notes.
5. `./check.sh`; `readiness | jq '{ready, complete, unset}'` here.

## Verification

- `uv run --group dev pytest -q tests/test_readiness.py tests/test_skills.py tests/test_evals.py tests/test_retro.py tests/test_archive.py`
- `uv run --quiet --script scripts/sdlc.py readiness | jq '{ready, complete, unset}'` → `true,
  true, ["commands.build","commands.scan"]` on this repo.
- `wc -l skills/setup/SKILL.md` ≤ 150.
- `./check.sh` exit 0.
- At ship (paid, under its prompt): `sdlc.py run-cases 058` scopes `setup` and passes.

## Rollback

`git revert <sha>`: restores `SKILL.md` whole, removes `drafts.md`, the fixture, the case and the
two `readiness` keys. No host file, config key or trailer changes; clone sessions pick it up at
`/reload-plugins`.
