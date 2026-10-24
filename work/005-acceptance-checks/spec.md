---
id: 005
slug: acceptance-checks
kind: spec
created: 2026-10-24
updated: 2026-10-24
---

# 005 — Rerun a change's acceptance checks at ship · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. The file.** A change may hold `work/NNN-slug/checks.md`. Each `## <name>` section is one
   check, holding exactly one fenced `sh` block, the command, plus any prose saying why.
   `templates/checks.md` gives its shape, held to the one-shape rule by `tests/test_defaults.py`
   like every template:
   - no frontmatter, since `sdlc.py` reads no keys from it;
   - the plain-name title `# Checks`, as `notes.md` has `# Notes`;
   - a `>` note saying what the file is for and that `sdlc.py` reads each section's name and its
     one `sh` block;
   - one example section, `## <What the check proves, as its name>`, holding a `<Why …>` line and
     an `sh` block whose one line is a `<the command …>` prompt, so an untouched copy is an
     unfilled scaffold (`is_unfilled()`).

   It goes in `DOC_TEMPLATES`, so `config` lists it under `templates`, and a host may override it.
   It has no `TEMPLATE_READS` entry, since no heading is read by name. The factory's builder starts
   a change's `checks.md` from the same text, and a test pins that the two match, as one already
   does for `notes.md`.
2. **R2. Reading it.** `acceptance(folder) -> {"checks": [{name, command}], "problems": [...]}`
   never raises. Each of these is a problem naming the section:
   - a section with no `sh` block, or two of them;
   - a duplicate name;
   - a `checks.md` that is still an unfilled scaffold.

   No file means no checks and no problems. `check --strict` reports the problems. One test per
   problem.
3. **R3. Listing.** `sdlc.py checks <NNN>` prints `acceptance()` as JSON and runs nothing. It joins
   `READ_ONLY` and `ALLOW_RULES`.
4. **R4. Running.** `sdlc.py accept <NNN>`:
   - runs each check in file order with `sh -c`, from the change's checkout root, each with a
     300-second timeout;
   - prints JSON with `change`, `checks` (`name`, `command`, `exit`, `passed`, `seconds`, and
     `output`: the last 40 lines of stdout and stderr together) and `passed`;
   - exits 1 when any check fails or times out, or `acceptance()` has a problem, and 0 with no
     checks;
   - **treats a check that leaves the working tree changed** (compared with
     `git status --porcelain` before and after) **as failed,** naming what it left, because ship
     commits that tree.

   It is never in `ALLOW_RULES` or any skill's `allowed-tools`. Tests cover pass, fail, timeout, a
   dirty tree, no file, and a bad file.
5. **R5. Ship runs them.** In `/sdlc:ship` Step 1, after the gate:
   1. run `sdlc.py checks <NNN>`;
   2. when it lists any, show each name and command;
   3. then run `sdlc.py accept <NNN>`, named in prose with no rule, so the harness asks once with
      the list in view.

   A failure stops ship, as a failing gate does, with each failing check's name and output. Step 7
   reports each check by name. A change with no `checks.md` sees one line, "no acceptance checks",
   and nothing else. `test_skills.py` checks that ship runs `checks` before `accept`, that both come
   after the gate and before Step 2, and that no skill has a rule matching `sdlc.py accept`.
6. **R6. Docs.** These edits land word for word in both the defaults and this repo's copies:
   - **Stage 4's Acceptance bullet:** a check that can run is a section in the change's
     `checks.md`, which ship reruns. One that can't, such as looking at a rendered page, stays in
     `notes.md` as prose.
   - **Review Pass 1:** its opening clause and "A test only a revert can fail" point to
     `checks.md`, falling back to `notes.md`.
   - **`plugins/factory/agents/reviewer-test.md`:** asks for the check in `checks.md`, and runs
     each one itself, since the factory has no `sdlc.py`.
   - **`plugins/factory/agents/builder.md`:** writes it there.
   - **`docs/REFERENCE.md`:** `work/` layout and ship.
   - **`AGENTS.md`:** a sentence in the architecture map.
   - **This repo's `.sdlc/setup.json`:** re-recorded.
7. **R7. Dogfood.** This change keeps its own acceptance checks in
   `work/005-acceptance-checks/checks.md`, and its ship runs them.

## Design

`acceptance()` reuses `_section`-style parsing: `FENCE_RE`, and `is_unfilled()` for the scaffold.
It lives beside `open_items()`. `cmd_checks` and `cmd_accept` find the folder with `change_dirs()`,
by `names_change()`. `cmd_accept` takes the checkout root as the folder's `parent.parent`, so a
check runs in the change's own worktree. It runs
`subprocess.run(["sh", "-c", cmd], cwd=root, timeout=300, capture_output=True)` and compares
`git status --porcelain` before and after.

The script judges by exit code alone; a check asserts inside its own command (`grep -q`, `test`).
Ship shows the list read-only, then runs `accept` under the one prompt. Its WAIT is unchanged.

The issue already renders every `*.md` in the folder. `ARTIFACT_ORDER` gains `checks.md` after
`notes.md`, so the checks are archived where people read them.

## Contracts touched

- **Narrow `allowed-tools`:** `checks` gets an exact rule; `accept` gets none on purpose, and a
  test pins that. This **changes what ship runs** (Tier 2): agent-written commands run only after
  you've seen them and answered a prompt. That's the same footing as `commands.check` today.
- **Every command in a bash block has a rule:** kept, because `accept` is named in prose, as
  `commands.check` is.
- **`READ_ONLY` and the allowlist:** adding `checks` to `ALLOW_RULES` makes every host's
  `readiness` report `permissions: missing` until its next `/sdlc:setup`. That's the same intended
  nudge 002 gave for `drift`.
- **The gate is offline and deterministic:** the gate is untouched; checks are the change's own,
  outside `commands.check`.
- **The `work/` layout:** one optional file. `TIER_ARTIFACTS` is unchanged, because a check is never
  required.
- **One shape for the shipped docs:** `templates/checks.md` follows it (`tests/test_defaults.py`).
- **The defaults track this repo's copies:** both edits are word for word.
- **Logic a permission rule must cover goes in the script:** the running, timing and dirt check are
  all in `cmd_accept`.
- **Nothing local:** neutral examples.

## Alternatives rejected

- **An allow rule for `accept`:** agent-written commands would run unasked, before the WAIT where
  you'd first see them.
- **One prompt per command:** pass or fail becomes the model's reading rather than the script's.
- **`checks.toml` or a `checks/` folder:** neither shows in the issue, and the folder needs an
  interpreter per file.
- **An `expect` output field:** a check asserts within its own command, so nothing parses output.
- **Rerunning earlier changes' checks:** they're acceptance checks, which is what the suite exists
  not to be.
- **A nudge for prose records in `notes.md`:** prose can't be told from a check reliably.

## Verification

```bash
./check.sh                                                   # all pass
uv run --group dev pytest tests/test_acceptance.py -q        # R1–R4
uv run --quiet --script scripts/sdlc.py checks 005           # this change's own checks, listed
uv run --quiet --script scripts/sdlc.py accept 005           # each passes, the tree unchanged
```
