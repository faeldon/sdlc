---
id: 036
slug: review-depth-by-risk
kind: spec
created: 2026-11-03
updated: 2026-11-03
---

# 036 — Review depth set by what a change touches · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Sensitive paths (seed 2026-11-03-4):

1. R1. A `[review]` config section with `sensitive` (paths whose changes always get the deep
   review) and `irreversible` (paths a revert doesn't undo), each a list defaulting to `[]`,
   resolved by `load_config()` and shown by `config`. A test covers the defaults, a host's values,
   and a value that isn't a list of strings, reported, not raised.
2. R2. An entry ending in `/` matches every path under it; any other entry is an `fnmatch` glob
   over the repo-relative path (`*` crosses `/`). A rename counts by both its old and new path. One
   function, `risk_paths(paths, patterns)`, with a test for each form.
3. R3. `preflight` gains a `risk` part, `_risk_report()`, from the change's diff against
   `git.base` (`changed_paths()`, as `nits --change`): `sensitive` and `irreversible` (the matched
   paths) and `deep` (true when `sensitive` is non-empty). With neither key set it is empty and
   `deep` false. Tests cover both.
4. R4. On a deep diff ship always runs `commands.build` when one is set, whatever `build_when`
   says, and always runs the fresh-context review (R6); its WAIT question names the sensitive
   paths, computed by `cmd_ship_question()` itself from the diff, so the skill can't leave them
   out: `touching sensitive paths a, b and c` (the first five, then `and N more`). A test pins the
   clause with and without a match.
5. R5. A tier never changes from risk; sensitivity deepens the review only.

Fresh-context review (seed 2026-11-03-5):

6. R6. The plugin ships one agent, `agents/reviewer.md` (`sdlc:reviewer`): tools `Read`, `Grep`
   and `Glob`, nothing that writes or runs commands; a prompt holding it to the review guide's
   reporting rules (evidence `path:line`, the bug's class, a rank and a pass) and returning
   findings as text in `findings.md`'s section shape. Ship runs it on a deep diff through `Agent`
   with `subagent_type: "sdlc:reviewer"`, its prompt holding the diff, the intent or spec, and the
   review guide's and repo's review doc's paths, nothing of ship's own reasoning. `Agent` joins
   ship's `allowed-tools`.
7. R7. Each finding it returns goes into `findings.md` with a new optional line, `By: fresh`; a
   section without one is ship's own. One ship's passes confirm takes ship's proposed disposition
   like any; one they don't is proposed `wrong`, with a `Reason:` saying why, which the person can
   overturn. `Sdlc-Findings` gains `fresh=<n>` (its findings) and `fresh_wrong=<n>`; old trailers
   parse unchanged. `findings_entries()` accepts `By:` and reports any value but `fresh`. Tests.
8. R8. When `Agent` is unavailable or the run fails, ship says so in Step 4, `findings.md`'s note
   gets a `Fresh review: skipped, <why>` line, and the WAIT question carries
   `without the fresh review (<why>)`, so a deep diff never lands with its review silently
   missing. A test pins the clause.

How to undo (seed 2026-11-03-6):

9. R9. When `risk.irreversible` is non-empty, ship drafts a `How to undo:` paragraph in the commit
   message after the body (for Tier 2, from `plan.md`'s Rollback), naming each matched path and
   what reverses it, and the WAIT question reads `with how to undo it shown`, computed by the
   script. A test pins the clause.

Setup, docs and the seeds:

10. R10. `/sdlc:setup` asks for both lists, offering candidates it finds (CI workflow files,
    release scripts, `migrations/`), and writes only what the person approves. The keys join
    `READS_CONFIG` for `sdlc:ship` (`review.sensitive`, `review.irreversible`) and `sdlc:setup`.
11. R11. `landing_reach()` reports a change to the core `agents/` as `agents` (`sdlc:<name>`),
    beside the factory's, with a test.
12. R12. `docs/REFERENCE.md` (the `[review]` keys and their matching, the `risk` part, `By: fresh`,
    the trailer keys), `guide/process.md` and `guide/review.md` (risk deepens the review; the fresh
    reviewer's findings count like any) and `AGENTS.md` (the core plugin's one agent, and ship as a
    skill that spawns one) say what changed.
13. R13. This repo's own config sets `sensitive = [".claude-plugin/", ".claude/settings.json",
    "scripts/trackers/", "check.sh"]` and `irreversible = ["defaults/", "templates/"]`: what a host
    receives through setup and keeps after a revert.
14. R14. Seeds 2026-11-03-5 and 2026-11-03-6 are deleted from the register in this change's
    commit, and 2026-11-03-7's `After: 2026-11-03-6` line with them, since this commit meets it.

## Design

- **`load_config()`** gains `CONFIG_KEYS["review"] = {"sensitive": [], "irreversible": []}`, both
  in `LIST_KEYS`, validated as `release.version_files` is.
- **`risk_paths()`** is pure; `_risk_report(root, path)` feeds it the diff's paths the way
  `_nits_report()` builds them.
- **`cmd_ship_question()`** computes the sensitive list and the irreversible hit itself; whether
  the fresh review was skipped comes in as `--fresh-skipped "<why>"`, since only the skill knows the
  `Agent` call failed. `ship_question()` renders each clause.
- **`findings.md`:** `FINDING_KEYS` gains `By`; `findings_trailer()` appends `fresh=` and
  `fresh_wrong=` after the dispositions; retro's `_add_findings()` sums them only over trailers
  carrying them, as `answered`.
- **The reviewer agent** is `agents/reviewer.md` at the plugin root, which
  `claude plugin validate --strict` checks; its prompt is generic, reading whichever review guide
  and review doc paths ship hands it.

## Contracts touched

- **A new config key:** read only through `load_config()`, named in `READS_CONFIG`. Keys are added,
  none renamed or retired, so `RETIRED_KEYS` and `drift` have nothing to break.
- **Narrow `allowed-tools`:** `Agent` is a tool, not a `Bash(...)` rule; the rules-coverage tests are
  unaffected. The reviewer's own `tools:` has nothing that writes or runs commands.
- **Confirm before writing:** the reviewer writes nothing; its findings reach `findings.md` through
  ship's existing exception (035), and every disposition is still approved at the WAIT.
- **One WAIT, worded by `preflight --question`:** the new clauses render in `ship_question()`.
- **Mechanism vs. judgment:** whether a diff is sensitive or irreversible is the script's; only the
  review itself is the model's.
- **The metrics trailer is a contract:** extended with `fresh` and `fresh_wrong`, never redefined.
- **The base branch:** the diff is taken against `trunk`, never a literal `main`.

## Alternatives rejected

- **An Important that can't be dismissed on a sensitive diff:** it would block on an unconfirmed
  fresh finding, the noise the person should be able to answer. The WAIT naming the paths, the build
  always running and the fresh review are the deep review.
- **Raising the tier from risk:** a tier sizes paperwork, set at intent; a risky path found at ship
  can't grow a spec retroactively.
- **A `general-purpose` or `Explore` subagent:** the first can edit, the second locates code rather
  than judging it. A plugin agent with a fixed tool list makes "writes nothing" structural.
- **One list for both:** release scripts are risky but revert cleanly; files setup copies into hosts
  are routine but don't revert. Different questions.
- **The fresh review on every change:** the person chose sensitive diffs only, so routine ships pay
  nothing.

## Verification

- `./check.sh` passes, its own exit code read, not piped.
- `uv run --quiet --script scripts/sdlc.py preflight 036` from this worktree shows a `risk` part;
  with R13's config this change's own diff (it touches `.claude/settings.json` and `templates/`)
  is `deep: true` with `irreversible` matched.
- `sdlc.py config` shows `review.sensitive` and `review.irreversible`; `drift` reports nothing
  after `record`.
- Shipping 036 runs its own deep flow: the build check (none configured, said so), the fresh
  reviewer, a `How to undo:` paragraph, and the clauses in the WAIT.
