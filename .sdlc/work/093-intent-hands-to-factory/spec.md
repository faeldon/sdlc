---
id: 093
slug: intent-hands-to-factory
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 093 — Intent offers the factory as a way to build the change, with no plan mode · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code:

- `factory.py start` refuses a Tier 1 that isn't at `plan` or `build`, and a Tier 2 that isn't at
  `plan`, `design` or `build` (`STARTS`, `plugins/factory/scripts/factory.py:113`). `new`
  scaffolds `stage: plan`, so a change that nobody plans by hand stays startable.
- `.sdlc/factory.toml` is optional. With no file, `factory.py`'s `load_config()` returns its
  defaults (`factory.py:285`), so whether the file exists says nothing about whether the factory
  is installed.
- `sdlc.py config` says nothing about the factory today (`cmd_config()`, `scripts/sdlc.py:582`).
  The only place the core reads `enabledPlugins` is `landing_reach()`'s note, and that note covers
  this repo alone.
- `metrics.py`'s `_reply()` classes an answer as `approve` when it matches `APPROVE_RE`, which
  starts `^\s*(yes|…)\b`, so `yes, by hand` and `yes, for the factory` both read as a yes
  (`scripts/metrics.py:96`, `:262`).
- The `intent` case's grader `asks-the-question.md` matches `Create this as Tier [0-2] change
  \d{3,}-`, and the new wording keeps that.

1. **R1.** `sdlc.py config` prints a top-level `factory` object, `{"enabled": bool, "scope":
   "local" | "project" | "user" | null}`. The value comes from the `enabledPlugins` maps of three
   files: `.claude/settings.local.json` and `.claude/settings.json` in the main checkout
   (`main_root()`), then `~/.claude/settings.json` (`Path.home()`, as `metrics._project_dirs()`
   finds `~/.claude`). The first file whose `enabledPlugins` has any key starting `sdlc-factory@`
   decides. `enabled` is that key's value being `true`, and `scope` names the file it came from.
   The new test `test_config_reports_the_factory_by_scope` fails unless each scope is reported
   when it is the only one set, and unless a `false` in `settings.local.json` beats a `true` in
   the user's file.
2. **R2.** If no file names the factory, a file is missing or won't parse, or `enabledPlugins`
   isn't an object, `config` prints `{"enabled": false, "scope": null}` with no traceback and no
   warning, and still exits 0. `test_config_reports_no_factory_without_settings` fails on a
   traceback, a non-zero exit, or `enabled: true`. Getting this wrong only hides an option, so an
   unreadable file reads as no factory.
3. **R3.** Finding the factory reads those three files and does nothing else. It runs no
   subprocess (`claude` included), touches no network, and imports and reads nothing under
   `plugins/`. `test_sdlc_loads_nothing_from_plugins` keeps passing. The new
   `test_factory_detection_runs_nothing` patches `subprocess.run` to raise and checks that
   `factory_enabled()` still answers.
4. **R4.** When `factory.enabled` is false, intent's Step 4 question is the one asked today. A
   Tier 1 ends `…off <git.base>, then start plan mode? (yes / yes, without plan mode / change the
   tier / edit a section)` and a Tier 2 ends `(yes / change the tier / edit a section)`.
   `test_spec_and_a_tier_one_intent_start_plan_mode_after_their_wait` keeps passing unchanged, and
   the new `test_intent_asks_as_before_without_the_factory` pins both strings in the WAIT section.
5. **R5.** When `factory.enabled` is true, the question gives both paths, with the manual one
   first:
   - a Tier 1 ends `…off <git.base>, then plan it here or hand it to the factory? (yes, by hand /
     yes, for the factory / change the tier / edit a section)`;
   - a Tier 2 ends `…off <git.base>, then write its spec here or hand it to the factory? (yes, by
     hand / yes, for the factory / change the tier / edit a section)`.

   That makes four answers each time, and `yes, without plan mode` isn't offered. The new
   `test_intent_offers_the_factory_when_it_is_enabled` pins both strings and the `factory.enabled`
   condition in the WAIT section. `test_every_wait_asks_in_a_dialog` still counts 2 to 4 answers.
6. **R6.** `yes, by hand` does exactly what `yes` does today. The skill calls `EnterWorktree`,
   then calls `EnterPlanMode` for a Tier 1, or names `/sdlc:spec` for a Tier 2. The new
   `test_intent_by_hand_is_the_old_yes` fails unless Step 6 sends `yes, by hand` down the same
   branch as `yes`, for each tier.
7. **R7.** `yes, for the factory` creates the change in the same way: `new … --worktree`,
   `commands.worktree_setup` in a subshell, the `Edit` of `intent.md` with the approved
   frontmatter lines, the `[building]` tags in the register, and `sync`. Two things differ: the
   skill never calls `EnterWorktree` or `EnterPlanMode`, and the session stays in the checkout it
   started in. Step 6 then gives the next action as `/sdlc-factory:build NNN`, run from the main
   checkout or in the supervisor session already running there. `stage:` stays `plan`. The new
   `test_intent_for_the_factory_stays_in_the_main_checkout` fails unless Step 5 skips
   `EnterWorktree` for that answer, and Step 6's factory branch names `/sdlc-factory:build` and
   never `EnterPlanMode`.
8. **R8.** The factory answer approves the same things the manual one does: the change, its
   worktree and its issue. Intent never runs the factory. No `Bash(...)` rule is added to intent's
   `allowed-tools`, the skill names no `scripts/factory.py` (the existing cross-plugin check in
   `tests/test_skills.py`), and `/sdlc-factory:build` keeps its own WAIT. The new test asserts
   that intent's `allowed-tools` holds no rule naming `factory`.
9. **R9.** Both new answers read as approval in metrics. The new
   `test_both_intent_yes_answers_read_as_approval` (`tests/test_metrics.py`) fails unless
   `_reply("yes, by hand")` and `_reply("yes, for the factory")` are both `approve`.
10. **R10.** The intent skill reads the new key from `config`, never from a guess.
    `READS_CONFIG["sdlc:intent"]` gains `factory.enabled`, and
    `test_skills_read_host_specifics_from_config` fails if the skill stops naming it.
11. **R11.** This is nit 2026-11-17-6. A new skills' case, `evals/intent-product/` tagged
    `[intent]`, runs `/sdlc:intent` on a new fixture, `evals/fixtures/product/`. The fixture has a
    `main` file and commits a `.sdlc/PRODUCT.md` with two open outcomes, `O1` and `O2`, in the
    format `product_items()` reads, using neutral content about drafts. It has these graders:
    - the suite's never-* graders and `asks-config`;
    - `asks-the-question`, a regex on the last message for `Create this as Tier [0-2] change
      \d{3,}-.*serving (O\d+ \(|no outcome)`;
    - a judgment grader that fails if, before its final question, the reply asks the person which
      outcome the change serves, or shows no `serves:` line with where it came from.

    `test_every_fixture_passes_check` runs `check --strict` on the new fixture, and
    `test_a_stop_case_keeps_every_never_write_grader` covers the case. In both fixtures the run's
    `HOME` has no factory enabled, so both cases also check R4's wording.
12. **R12.** The docs say what changed:
    - The README's "Factory and manual, change by change" says that with the factory enabled,
      intent's question offers `yes, for the factory`, which skips plan mode and leaves the
      session in the main checkout.
    - `plugins/factory/README.md`'s account of `/sdlc:intent` says the same.
    - `docs/REFERENCE.md` lists `config`'s `factory` object, its three files and its precedence.

    `sdlc.py context` names those docs for this diff, and ship shows the edits.
13. **R13.** `./check.sh` passes, and `sdlc.py drift` reports nothing, since nothing in
    `defaults/` or `guide/` changes.

## Design

**Finding the factory: `factory_enabled(home)` in `scripts/sdlc.py`.** This is a pure reader. It
takes the main checkout's path and returns `(enabled, scope)`, walking the three files from most
to least specific: `home/.claude/settings.local.json`, `home/.claude/settings.json`, then
`Path.home()/.claude/settings.json`. Each file is read with `read_text(encoding="utf-8")` and
`json.loads`. If any step fails (`OSError`, `ValueError`), or `enabledPlugins` isn't a dict, the
file is skipped. In the first file that has a key starting `sdlc-factory@` (any marketplace name,
so a host that installed from a fork still counts), the result is `value is True`. If no file has
one, the result is `(False, None)`. The precedence is Claude Code's own, local over project over
user, so a person who turns the factory off for one repo doesn't get offered it there.
`cmd_config()` calls this function once with `main_root(root)`, and the result goes into `out`
next to `git`. It reads the main checkout's files because that is where the supervisor runs and
where the factory answer leaves the session. `settings.local.json` is untracked, so a change
worktree doesn't have it.

This finds the factory wherever it was installed through `/plugin` or `claude plugin install`, at
any scope, and that is the case that was missed: 079's `.claude/settings.json` misses a user-scope
install. It doesn't find a factory loaded with `claude --plugin-dir`, which writes no settings.
That session gets today's question, and the person can still run `/sdlc-factory:build` after
answering `yes, without plan mode`.

**Intent's Step 0** already runs `config`, so it also notes `factory.enabled`. That one line is
everything intent knows about the factory.

**Intent's Step 4.** The current Tier 1 paragraph stays as the form used when the factory isn't
enabled. A new paragraph covers `factory.enabled: true` and gives the two R5 endings for Tier 1 and
Tier 2. The question opens the same way in every form (`Create this as <tier> change NNN-<slug>
…, serving …, [opening its GitHub issue …,] in a new worktree and branch NNN-<slug>
off <git.base>`), so the `serving` clause, the issue clause and the case's regex all stay as they are.
The dialog rule is unchanged. Only a chosen `yes, …` approves, so `yes, for the factory` approves,
and a dismissed dialog doesn't.

**Intent's Step 5** splits in one place. The existing paragraph that says "Then move **this
session** into the worktree … `EnterWorktree`" starts "Unless the answer was `yes, for the
factory`". Everything before and after it is the same for both answers. The edit to `intent.md`
and the register still go to absolute paths inside the worktree that `new` printed, and
`sync <NNN>` finds the change from any checkout through `change_dirs()`.

**Intent's Step 6** gains a branch for each answer:

- `yes` or `yes, by hand`, Tier 1 → `EnterPlanMode`, as today.
- `yes, without plan mode`, offered only without the factory → as today.
- Tier 2 by hand → "run `/sdlc:spec` next."
- `yes, for the factory`, either tier → "The session stays here. Run `/sdlc-factory:build NNN`
  from the main checkout, or hand it to the supervisor already running there. Its builder plans a
  Tier 1, and its spec-writer drafts a Tier 2's spec before its own gate."

The sentence "The session is now in the worktree" applies only to the by-hand answers.

**The case** (R11) uses a `main` fixture, the same shape as `set-up`: `scaffold.sh` commits it on
`main` and runs `record`. Its `.sdlc/config.toml` sets only `[archive] target = "none"` and
`[git] attribution = false`, so `readiness` doesn't get in the way. `.sdlc/PRODUCT.md` comes from
`defaults/PRODUCT.md`'s shape, with two outcomes about drafts. The prompt is the existing intent
prompt's, with a Problem that points at one outcome, so a run that proposes `serves: [O1]` without
asking and names `O1 (…)` in its question passes.

**Edge cases.**
- If the person answers `yes, for the factory` and then runs `/sdlc:spec` or plan mode anyway,
  nothing stops them. The change is at `plan` either way, and both paths start from there.
- If the session started in another change's worktree, it stays there. `factory.py` finds the new
  change's worktree from any checkout (`change_root()`).
- A Tier 0 never reaches Step 4.

## Contracts touched

- **Skills: exactly one WAIT, asked in an `AskUserQuestion` dialog with 2 to 4 answers, where only
  a chosen yes approves** (`test_every_wait_asks_in_a_dialog`). There is still one WAIT heading.
  Every form has 3 or 4 answers, and each approving answer starts with `yes`. Five answers
  (`yes, without plan mode` beside both new ones) would break the limit. That's why the factory
  form drops it, and that's the reason for open question 4's answer.
- **Confirm before writing.** Nothing is written before the yes, and the factory answer writes
  exactly what the manual one does. Entering a worktree or plan mode writes nothing, so skipping
  them changes no write.
- **Narrow `allowed-tools`.** No rule is added. `config` already has one, and `EnterWorktree` and
  `EnterPlanMode` stay listed because the by-hand answers use them.
- **Each skill runs `config` and names its keys** (`READS_CONFIG`). `factory.enabled` is added
  (R10).
- **The factory is optional by being installed or not, and `sdlc` loads nothing from `plugins/`**
  (`test_sdlc_loads_nothing_from_plugins`). The core now knows whether the factory is enabled, but
  only from Claude Code's settings files, never from the factory's code or files. It never needs
  the factory: with none, every path is today's (R3, R4).
- **A tracker never reads `.sdlc/`, and core never calls `gh`.** Not touched.
- **The scripts run on Windows.** `Path.home()`, `read_text(encoding="utf-8")`, no new subprocess,
  and nothing written. The new tests that touch only files are marked `portable`.
- **Nothing about a project or a workspace.** The fixture's product doc is about neutral drafts,
  and the tests use `tmp_path` for `HOME`, never a real home path.
- **Skills' cases are never in `check.sh` or CI, and `run-cases` is never allowed unasked.** The
  new case is only a folder under `evals/`. `tests/test_evals.py` builds its fixture offline.
- **Metrics read a dialog's answer in a gated span as the gate.** Both new answers match
  `APPROVE_RE` (R9). No event or trailer format changes.
- **`.claude/settings.json` is sensitive** (`[review] sensitive`). This change reads it and never
  edits it. `uninstall` and setup's `attribution` stay its only writers.

No invariant needs to change.

## Alternatives rejected

- **Treat `.sdlc/factory.toml` as the signal.** The factory runs on its defaults without that
  file, so a host with the factory installed and no file would never see the option. A file left
  behind after an uninstall would show an option that can't be used.
- **`claude plugin list` from `config`.** This runs a slow subprocess on every skill's Step 0. It
  goes outside git, depends on the CLI being on `PATH` in the sandbox, and has the core run
  `claude`, which only `factory.py agent` does.
- **Only `.claude/settings.json`'s `enabledPlugins`, as 079 set it.** This misses a user-scope
  install, which is how most hosts would get the factory.
- **Let the skill decide whether the factory is loaded from the skills it can see in the
  session.** That is judgment, can't be checked by a test, and differs between the dialog and the
  case runs. A script field can be pinned.
- **Record the path in frontmatter (`mode: factory`).** Left for the person (open question 2).
  It's left out of this design because it touches `check`, the board, status, the intent template
  and `TEMPLATE_READS` for a field that `Sdlc-Mode` on the `Close` commit already records once a
  run happens.
- **A per-repo default for which yes comes first.** That needs a new config key, a drift entry
  and a setup question just to reorder two buttons. The intent's own Outcome puts the manual one
  first, and a host that always uses the factory clicks the second answer.
- **Keep `yes, without plan mode` beside the factory answer.** That makes five answers, past the
  dialog's four. Its main use, filing a change for someone else to build, is now
  `yes, for the factory`. It stays in the form used without the factory, which is what the
  constraint requires.
- **Have intent start the factory run.** That's ruled out by the intent's constraints. It would
  also put a second approval behind one yes and skip `/sdlc-factory:build`'s own WAIT.

## Verification

```bash
./check.sh
```

Healthy output: ruff and the format check are clean, pytest is all green (including the new
`test_config_reports_the_factory_by_scope`, `test_config_reports_no_factory_without_settings`,
`test_factory_detection_runs_nothing`, `test_intent_asks_as_before_without_the_factory`,
`test_intent_offers_the_factory_when_it_is_enabled`, `test_intent_by_hand_is_the_old_yes`,
`test_intent_for_the_factory_stays_in_the_main_checkout`,
`test_both_intent_yes_answers_read_as_approval`, and `test_every_fixture_passes_check[product]`),
and `claude plugin validate --strict` passes.

```bash
uv run --quiet --script scripts/sdlc.py config | jq .factory
```

In this repo this prints `{"enabled": true, "scope": "project"}`, because `.claude/settings.json`
enables `sdlc-factory@sdlc`. With `HOME` set to an empty directory, in a scratch repo with no
`.claude/`, it prints `{"enabled": false, "scope": null}`.

```bash
uv run --quiet --script scripts/sdlc.py drift
```

This reports nothing.

The skills' cases for this change's scope, the `intent` tag (`intent` and `intent-product`), are
run through `run-cases`. Ship names that command and the person approves it at its prompt,
because it's a paid run. Healthy output: every grader passes in both cases, and
`asks-the-question` in `intent-product` matches a `serving O1 (…)` clause.

Manual check, in a session with the factory enabled: `/sdlc:intent` on a small change offers
`yes, by hand / yes, for the factory / change the tier / edit a section`. After `yes, for the
factory`, the session's working directory is still the main checkout, no plan mode starts,
`intent.md` reads `stage: plan`, and the last line names `/sdlc-factory:build NNN`.

Boundaries:
- **Always:** the factory form shows only when `config` says `factory.enabled: true`, and both
  answers create the change the same way.
- **Ask first:** any change to which yes comes first, or adding a frontmatter field.
- **Never:** start a factory run from intent, write to a settings file, or run `claude` from
  `sdlc.py`.
