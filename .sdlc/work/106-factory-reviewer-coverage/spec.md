---
id: 106
slug: factory-reviewer-coverage
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 106 — Factory review reads the tests and sees the new cards · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Two corrections to the intent's *Affected*, both checked in the code. `[ui]` lives in
`.sdlc/factory.toml` (`factory.py`'s `_ui()`, read from the base branch's copy), not in
`.sdlc/config.toml`. It is documented in `plugins/factory/README.md`, *Configuration*, not in
`docs/REFERENCE.md`, which has no `[ui]` section. This change edits those two files instead.

**The test reviewer at the light depth**

1. **R1.** Leave `[light] reviewers` unset and give a Tier 2 change a diff that touches no
   sensitive path. Its light rounds then expect `code` and `test`. On the first unreviewed build,
   `verdicts` reports `depth: light` and `missing: ["code", "test"]`. A round holding only
   `code.md` is incomplete, and `next` stays `review` with `missing: ["test"]`. Test:
   `test_a_tier_2_light_round_includes_the_test_reviewer`. It fails while `missing` is `["code"]`
   alone, or while a code-only round reads as complete.
2. **R2.** A Tier 1 change at the light depth keeps today's reviewers. With `[light] reviewers`
   unset, `missing` is `["code"]`. The existing `test_a_diff_touching_no_sensitive_path_runs_light`
   stays green unchanged, and a new Tier 1 case in R1's test fails if `test` appears.
3. **R3.** A change whose `tier:` can't be read (None) also gets today's light reviewers. R1's
   test has a case for this.
4. **R4.** When a host sets `[light] reviewers`, that list is used exactly at both tiers. Nothing
   is added for a Tier 2. Test: `test_a_set_light_list_is_kept_at_either_tier`. It fails if
   `test` joins a Tier 2 run whose `[light] reviewers = ["code"]` was set by hand.
5. **R5.** The Tier 2 default adds `test` only when `test` is among the full depth's `reviewers`.
   That way a light round never runs a reviewer the full depth doesn't. Test: R4's test, with
   `reviewers = ["code", "security"]` at the top level. It fails if `test` is expected.
6. **R6.** Running the test reviewer at the light depth never makes a run full. A Tier 2 light run
   whose rounds hold `code` and `test` (and `ui`/`ux` when they joined) stays `depth: light` in
   round 2. Test: `test_the_test_reviewer_never_deepens_a_tier_2_light_run`. It fails if
   `depth()`'s "a run never lightens" check counts `test` as a reviewer beyond `[light]`.
7. **R7.** `factory.py start` reports the light reviewers for this change's tier. So the build
   skill's one question (`<light reviewers>`) names `code, test` for a Tier 2, and `config`
   reports whether `[light] reviewers` was set. Test: R1's test reads `start`'s `light.reviewers`
   for a Tier 1 and a Tier 2 change.
8. **R8.** The landing review (`land-verdicts`) and `carry` judge rounds against the same tier's
   reviewers. They do this already by going through `_rounds_at_depth()`, and one assertion in R1's
   test pins it: `land-verdicts` after a resolved conflict lists `test` among `missing` for a
   Tier 2 light run.

**Fixture data for the UI review**

9. **R9.** `[ui]` takes a new key, `fixture`: a repo-relative path to a file or folder in the
   checkout. Its default is none. With it unset, `shots()` runs exactly as today, and the
   existing `test_shots_*` tests stay green unchanged. Test:
   `test_ui_fixture_is_checked_like_the_other_keys`. It fails if any of these is accepted rather
   than turned into a warning that leaves the default:
   - a non-string value
   - an absolute path
   - a path containing `..`
10. **R10.** When `fixture` is set, `shots()` puts a fresh copy of it at
    `.sdlc/reports/shots/<change>/<label>/fixture/` before it starts the server. It replaces only a
    copy it made itself, and fills `{fixture}` in `serve` with that copy's path, relative to the
    checkout and POSIX. `shots.json` records the filled command. Test:
    `test_shots_serve_a_fresh_copy_of_the_fixture`. A fake server writes into the copy, and the
    test asserts that:
    - the committed fixture is byte-identical afterwards;
    - a second label gets its own clean copy;
    - the recorded `serve` holds a relative path that names no machine.
11. **R11.** A `fixture` that doesn't exist in the checkout is a `problem` in `shots.json`, so the
    UI review is refused (the existing "never runs blind" path) and no server starts. A `serve`
    that names `{fixture}` while `fixture` is unset is a `config` warning. Test:
    `test_a_missing_fixture_refuses_the_ui_review`.
12. **R12.** This repo's `.sdlc/factory.toml` names a board fixture at `tests/fixtures/board/`.
    Its `serve` builds a scratch repo from that fixture and runs this checkout's own
    `scripts/sdlc.py board` in it. The fixture uses neutral examples only
    (`test_nothing_local.py` stays green).
13. **R13.** The board fixture holds a card in each state the board shows. Test:
    `test_the_board_fixture_shows_every_card_state`. It builds the scratch repo with the fixture's
    own build script and reads `board.state()` in-process. It fails if any of these is missing:
    - each column (`plan`, `design`, `build`, `test`, `ready`, `close`, `needs-you`);
    - a factory card with a step track (`progress` set from `runs/step.md`);
    - a stopped factory run;
    - a blocking decision pending;
    - an escalated change at `test`;
    - a shipped or dropped factory change whose decision was `ESCALATE` (the card's
      `was ESCALATE`);
    - a hand gate that is current and green, and one that is current and red;
    - a file that won't read.
14. **R14.** The plugin docs say what changed:
    - `plugins/factory/README.md` gains the `fixture` key in the `[ui]` block, its meaning, and the
      Tier 2 light default.
    - `skills/build/SKILL.md`'s line "default the code reviewer for 2 rounds" says the Tier 2
      default.
    - `test_the_build_verifies_before_rework_and_states_its_depths` stays green.

## Design

**Light reviewers by tier.** One new function, `light_reviewers(cfg, tier) -> list[str]`, owns the
rule:

- If `[light] reviewers` was set, return it as set.
- Otherwise, for `tier == 2` with `test` in `cfg["reviewers"]`, return `["code", "test"]`, in
  `REVIEWERS` order: the default list plus `test`.
- Otherwise return the default list.

`load_config()` records whether `[light] reviewers` was set as `cfg["light"]["chosen"]` (bool).
This is an added key in `config`'s JSON. Nothing existing is renamed.

- **Where the tier comes from.** `depth(root, cfg, rounds, starts, tier)` takes the tier.
  `_rounds_at_depth()` reads it from `intent.md`'s frontmatter with the existing `frontmatter()`.
  Every caller (`loop_state`, `cmd_carry`, `cmd_land_verdicts`, and `agent` through `loop_state`)
  already goes through that function, so one place changes.
- **Edits inside `depth()`.**
  - The `chosen` depth's reviewers at `light` become `light_reviewers(cfg, tier)`.
  - The `beyond` test subtracts `set(light_reviewers(cfg, tier))` rather than
    `set(light["reviewers"])`. That is R6: without it, a Tier 2's own `test.md` would make the run
    full in round 2.
- **`cmd_start`** already reads the tier. It reports `light.reviewers` as
  `light_reviewers(cfg, tier)`, so the gate's question and `models_at` match what will run.
  `max_runs()` is unchanged: it counts the full depth, and R5 keeps the light reviewers a subset
  of the full ones.
- **Models.** `model_for` needs no change. `test` is in `SCALED`, so it runs on `sonnet` for a
  Tier 2 at either depth. The added cost is one sonnet reviewer per light round of a Tier 2, at
  most `[light] rounds` (2 by default).

**Edge cases.**

- A run that is mid-way when the upgrade lands now expects `test` on its current Tier 2 light
  round. `verdicts` then asks for `test` on that round, which is the intended outcome.
- Earlier rounds of such a run are recomputed as incomplete. Only `carry` reads past the last
  round (`done[-1]`), so it may carry from an older complete round, or from none.
- An already decided run is `done` before any of this is read.
- A restart counts its rounds from the restart as today (`starts`). Its new rounds include `test`.

**The fixture.** `_ui_table()` accepts `fixture` as a non-empty string. It warns, and leaves the
default None, for a path that is absolute or contains `..`. The "must be a table of …" message
names `fixture` too. `load_config()` warns when `serve` contains `{fixture}` but `fixture` is unset.

`shots()` works as follows when `ui["fixture"]` is set:

1. It checks the path exists under `root`. If not, it records a `problem` and starts no server.
2. It removes `where / "fixture"` if an earlier failed attempt left it. That folder is under
   `.sdlc/reports/`, which ignores itself, and only `shots` writes there.
3. It copies the fixture in with `shutil.copytree` (a folder) or `copy2` (a file).
4. It fills `serve` with `port=` and `fixture=`: the copy's path relative to `root`, as POSIX.

The reuse rule ("a label already shot without a problem is reused") is unchanged: no copy is made
when no shot is taken. The server still runs with `cwd=root`, `_sh()`, its own process group, and
the same stop.

**This repo's fixture.** The board reads git:

- `change_dirs()` finds a change on its branch through `worktrees()`;
- `hand_gate()`'s `current` compares the record against the branch's build;
- `ready_to_close()` walks worktrees.

So plain files can't show the gate badge or a ready-to-close card. `tests/fixtures/board/` holds:

- `changes/<NNN-slug>/`: each change's folder contents. These are the data: `intent.md`,
  `runs/step.md`, `decision.md`, `decision-1.md`, `build/gate.md`, and so on, with neutral slugs.
- `build.sh <dir>`: plain `sh` and `git`, in the style of `evals/scaffold.sh`. It runs
  `git init -b main` in `<dir>`, commits a base with a `.sdlc/config.toml` whose
  `[commands] check` is fixed per change. It puts each change on its own branch, in a worktree
  under `.claude/worktrees/` where the state needs one, and writes current hand-gate records by
  running `sdlc.py gate` there. Commits use `-c user.name=fixture`, in the scratch repo only.
- `serve.sh <dir> <port>`: runs `build.sh <dir>`, then `cd <dir>` and
  `exec uv run --quiet --script <checkout>/scripts/sdlc.py board --port <port>`. The script path is
  found from `serve.sh`'s own location, so the board shown is the change's own.

`.sdlc/factory.toml`'s `[ui]` then reads
`serve = "sh tests/fixtures/board/serve.sh {fixture} {port}"` and
`fixture = "tests/fixtures/board/changes"`. `paths` and `shoot` are as today. `paths` gains
`tests/fixtures/board/`, so a change that adds a card state, and with it a fixture case, gets the
UI review.

The fixture's data is read from the change's checkout, not the base branch. That is deliberate: a
change that adds a state adds its fixture case in the same diff, and its shots show it.

R13's test runs `build.sh` into `tmp_path` and calls `board.state()` with `sdlc.py` loaded by
path, as `tests/test_board.py` does. It needs `sh`, `git` and `uv`, so it is skipped without them
and is not `portable`.

## Contracts touched

- **The depth rule: "a run never lightens", and the depth is set by the base branch's sensitive
  list** (`plugins/factory/README.md`, AGENTS.md *The factory*). The design stays inside it:
  - the light/full choice is still made only from `[review] sensitive` on the base branch and
    from earlier rounds;
  - the tier changes only which reviewers the light depth expects, never which depth a run gets;
  - R6 guards the one place the new reviewer could deepen a run by accident;
  - the tier comes from the change's own `intent.md`. A change could edit its tier, but only to
    *add* a reviewer at Tier 2. Lowering the tier to 1 was already the person's call at intent,
    and doesn't lighten anything relative to today.
- **`[ui]` is read from the base branch** (`_ui()`): "a change can't choose the command a UI review
  starts".
  - `fixture`, like every `[ui]` key, is read from the base branch's `factory.toml`.
  - Only the fixture's *contents* come from the checkout. The base branch's `serve` already runs
    the change's own `scripts/sdlc.py board`, so the change's own code is run either way, and a
    fixture adds no new command.
  - `build.sh` and `serve.sh` are files in the checkout that the base branch's `serve` names. A
    change can edit them, as it can edit `board.py` today. That trust is unchanged.
- **"No agent commits"; `factory.py gate` is the one place the factory runs a host's command.**
  - The commits are made by `build.sh`, which `[ui] serve` runs through `shots()`, the path that
    already runs `[ui]`'s commands. They land in a scratch repo under `.sdlc/reports/`, never the
    change's checkout. The `HEAD` check in `verdicts` reads the change's checkout, which they don't
    touch.
  - The scratch repo's `sdlc.py gate` runs its own `[commands] check`, not the host's.
  - No agent runs any of it.
- **"The eval and the review write only under `.sdlc/reports/`"**: the fixture's copy and its
  scratch repo are there, and the committed fixture is never written (R10).
- **The board writes nothing.** Unchanged: `build.sh` writes the scratch repo before the board
  starts, and the board only reads it.
- **Windows** (`tests/test_windows.py`): `shots()`'s copy and removal use `pathlib` and `shutil`.
  The removal handles read-only git object files with `rmtree(onexc=…)`. Any new `write_text`
  passes `newline="\n"`, and the recorded `{fixture}` path is `as_posix()`. The fixture's `.sh`
  scripts run through `sh`, as `[ui]` commands already do.
- **Nothing about a project** (`test_nothing_local.py`): the fixture's changes use neutral slugs
  and no change number from this repo's history.
- **Config keys.** `fixture` is a new key whose default (none) keeps today's behaviour. No key is
  renamed or retired, so no `RETIRED_KEYS` or deprecation entry is needed.
  `factory.toml` isn't in `defaults/` or `templates/`, so `drift` is untouched.

No invariant needs to change.

## Alternatives rejected

- **A `light_tier2` setting** (the intent's first open question). `[light] reviewers` already
  says which reviewers run light. A second key would mean two lists to keep in step, and a host
  that wants the old behaviour can set `[light] reviewers = ["code"]` (R4). The intent's own
  Outcome says "the default `factory.light` for a Tier 2", so it is a default, not a switch.
- **The test reviewer at the light depth for every tier.** Ruled out by the intent's constraint
  that a Tier 1 keeps today's reviewers. A Tier 1 has no spec of numbered requirements for the
  test reviewer to read against.
- **Making a Tier 2 always run full.** That would cost a security reviewer and a third round on
  every non-sensitive Tier 2, and break "depth follows risk".
- **The factory building the scratch repo itself** (a git-aware `fixture`). `factory.py` would
  then know what a board needs. The plugin knows nothing about what a host serves. A copied path
  and a `{fixture}` placeholder serve any dev server, and a host whose server needs a database
  seeded does that in its own `serve`.
- **A `--root` or `--fixture` flag on `sdlc.py board`.** That would add a host-facing flag to core
  for a test's sake. Running the board with its cwd in the scratch repo needs nothing new.
- **Serving the fixture in place, without a copy.** A server that writes would dirty the
  committed fixture and the change's diff, and the next shot would differ.
- **Reusing `evals/scaffold.sh` and `evals/fixtures/`.** That scaffold builds one change for a
  paid case, and its fixtures are pinned to `check --strict` by `test_evals.py`. A board with
  several changes in several states is a different shape, and coupling the two would make an eval
  edit break the UI review.

## Verification

```bash
uv run --group dev pytest tests/test_factory.py -q -k "light or tier or fixture or shots or depth"
uv run --group dev pytest tests/test_board.py -q -k fixture
uv run --group dev pytest tests/test_skills.py -q -k depths
./check.sh
```

What a healthy run looks like:

- The first three commands pass, the new tests included: R1–R8 in `test_factory.py`, R9–R11 in
  `test_factory.py`'s shots tests, and R13's board test.
- `./check.sh` ends with ruff clean, the formatter clean, every pytest test passing (the existing
  `test_a_diff_touching_no_sensitive_path_runs_light`,
  `test_a_restarted_light_run_stays_light_and_a_full_one_stays_full` and `test_shots_*` included,
  unchanged), and `claude plugin validate --strict` passing.

By hand, once:

```bash
uv run --quiet --script plugins/factory/scripts/factory.py config
```

This should report `ui.fixture: "tests/fixtures/board/changes"`, `light.chosen: false`, and no
warnings. Then:

```bash
sh tests/fixtures/board/serve.sh "$(mktemp -d)/fixture" 5199
```

With that running, opening `http://127.0.0.1:5199/` should show cards in every column, a step
track, a `was ESCALATE` card, and a green and a red gate badge. Ctrl-C stops it.

**Boundaries.**

- **Always:** a Tier 2 at the light depth gets the test reviewer unless the host chose
  `[light] reviewers`, and a set `fixture` is copied before every shot.
- **Ask first:** making the light depth apply to more than the reviewer list (its rounds, its
  models), or reading the tier from anywhere but the change's `intent.md`.
- **Never:**
  - change which depth a run gets;
  - add a reviewer for a Tier 1;
  - write the committed fixture;
  - let `factory.py` run git in a fixture;
  - start a server outside `shots()`.

