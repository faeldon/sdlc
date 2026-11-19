---
id: 187
slug: one-word-one-meaning
kind: spec
created: 2026-11-19
updated: 2026-11-19
---

# 187 — One meaning per word, and sdlc.py check becomes sdlc.py vet · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Tests can't check what a word means. They can check that a doc avoids a fixed list of worded
phrasings and names. So the vocabulary half of this change is checked in two ways. A term test
scans a fixed set of prose files for each retired phrasing (R10, R11). Any other wrong use is left
to ship's review, under REVIEW.md's *A doc's claim the change made false*.

Assumptions checked in the code: `sdlc.py check` is `cli_check()` (`scripts/sdlc.py`), listed in
`HELP_ORDER` and `READ_ONLY`. `ALLOW_RULES` is built from `READ_ONLY`. `permissions_status()` and
`cmd_readiness()` compare `ALLOW_RULES` against `.claude/settings.json`. The verifier is the role
`verifier` in `factory.py`'s `ROLES`, `FIXED_MODELS` and `agent --role`. Its tasks are `verify`
and `land-verify` (`TASKS`, `TASK_STEP`, `ROUND_PURPOSE`, `LAND_STEPS`, copied into
`factory_records.py`). Its agent is `plugins/factory/agents/verifier.md`, run as
`agent_name(role)`. Old records name it in `runs/costs.jsonl` rows (`role`), `runs/<role>.sessions`,
`runs/mended`, `runs/step.md` and `runs/land-step.md`. `[models]` in `factory.toml` is keyed by
role, and `_models()` warns on a role not in `ROLES`.

Nits taken in: 2026-11-19-41, 2026-11-19-44, 2026-11-19-52

**The command**

R1. `sdlc.py vet` does what `check` did: the same `■ Problems:` report, exit 0. With `--strict` it
exits 1 on any problem. `test_vet_strict_fails_on_a_problem` fails if not. The tests that ran
`check --strict` all run `vet --strict`: `test_sdlc.py`, `test_adoption.py`, `test_evals.py`,
`test_acceptance.py`, `test_config_resolution.py`, `test_deprecations.py`, `test_next_up.py` and
`test_retro.py`'s read-only loop.

R2. `sdlc.py check` is no longer a command and has no alias. argparse refuses it with exit 2.
`test_check_is_no_longer_a_command` fails if anything still answers to it. `HELP_ORDER` names
`vet` where `check` stood.

R3. `READ_ONLY` holds `vet` and not `check`. So `ALLOW_RULES`, and readiness's
`permissions.rules`, name `Bash(uv run --quiet --script */scripts/sdlc.py vet *)`.
`test_a_host_with_only_the_check_rule_is_missing_the_vet_rule` fails unless readiness reports
`permissions: missing` with that rule in `permissions.missing`, and `complete: false`, for a
settings file that holds every old rule. That is how setup comes to propose the new rule on a
host's next run.

R4. Every caller moves in this change:
- the bash blocks and `Bash(...)` rules of `skills/status`, `ship`, `spec`, `setup` and `health`;
- the factory build skill's prose;
- this repo's `.claude/settings.json`;
- the `set-up` and `product` eval fixtures' `.claude/settings.json`, so
  `test_the_set_up_fixture_is_complete` still holds;
- AGENTS.md, README.md, `docs/`, `guide/`, `.sdlc/SDLC.md` and the factory README.

`test_skills.py`'s existing rule tests fail on a moved command without its rule. The retired-names
test (R11) fails on any `sdlc.py check` left behind.

R5. `sdlc.py`'s module docstring lists `vet --strict`. It drops the `check --json` line, which
names a flag the command never had.

**The words**

R6. `docs/FEATURES.md`'s *Vocabulary* has one entry for each term below. Each says what the term
means now and what it never means. `test_every_vocabulary_term_has_an_entry` fails if one is
missing.
- `gate`: the host's commands only, `[commands] check` and the slow gate, run by ship,
  `sdlc.py gate` and the factory's `gate`.
- `slow gate`: `[commands] build`.
- `approval`: a person's yes at a WAIT.
- `WAIT`.
- `acceptance checks`: the commands `checks.md` holds, called "acceptance" after a doc's first use
  and on labels. They are never a person's yes.
- `vet`: `sdlc.py vet`, which checks each change folder against its tier and stage, the artifacts
  it owes and their frontmatter. It runs no command of the host's, so it is never a gate.
- `arbiter`: weighs each round's findings before the builder reworks. It is never the approver,
  which decides the whole change at the end.
- `verification`: the umbrella for did we build it right. It covers the gates, the reviews, the
  arbiter and the acceptance checks.
- `validation`: did we build the right thing. Milestones and the product's outcomes, which the
  retrospective judges.

The `gate` entry no longer says "or a person's approval at a WAIT". The entries for `stop`,
`Sdlc-Stage`, `Sdlc-AfterGate` and `Sdlc-Landed` use "approval" for a person's yes. They also say
that the trailer's own keys (`Sdlc-AfterGate`, the `gate=` count, `by=auto`) keep their names.

R7. "Approval", never "gate", for a person's yes. This covers:
- AGENTS.md: "a human gate at every stage that writes", the skills invariant's "as the gate", and
  "`check --strict` is a gate", which becomes "`vet --strict` refuses";
- both `plugin.json` descriptions and `marketplace.json`;
- `guide/process.md`, REFERENCE.md and the skills' and agents' prose.

The retired phrasings in R10 fail on any of them left behind.

R8. "Acceptance" always goes with a change's checks. The landing question's "its failed or skipped
skills' cases accepted as shown" becomes "… approved as shown". That changes `landing.py`'s
question, the land skill's text, and the asserts in `test_land.py` and `test_skills.py`. No
scanned doc says a yes "accepts" anything. `checks.md`, `sdlc.py checks`, `sdlc.py accept`,
`[commands] check` and `check.sh` keep their names.

R9. The slow gate. `commands.build` is "the slow gate" in prose:
- the guide's heading `#### The gate and the slower check` becomes `#### The gate and the slow gate`
  in `guide/process.md`, `defaults/SDLC.md` and this repo's `.sdlc/SDLC.md`;
- so do the guide's Stage 4 table row, `skills/setup/drafts.md`, `skills/health/SKILL.md`,
  REFERENCE.md's config block, and the `CONFIG_KEYS` and readiness comments in `sdlc.py`.

`sdlc.py record` is rerun from the change's checkout. `test_defaults.py` and the gate's `drift`
check fail if the guide, the defaults and `.sdlc/setup.json` disagree.

R10. A new term test, `test_no_doc_uses_a_retired_phrasing` in `tests/test_feature_map.py`, marked
`portable`. It reads the prose set with inline code spans and fenced blocks stripped. It fails,
naming the file, the line and the word to use instead, on any of these, matched case-insensitively:
- `\bverifier\b` (arbiter)
- `\bhuman gates?\b`, `\bWAIT gates?\b`, `\bapproval gates?\b`,
  `\bgates? at (a|the|every|each) (WAIT|stage)\b` (approval)
- `\bgated (skill|span)s?\b` (a skill with a WAIT, the WAIT's span)
- `\bslower (check|gate)\b` (slow gate)
- `\baccepted as shown\b`, `\byes accepts\b` (approved)
- `\b(the|its|a change's|the change's|own) checks\b` (acceptance checks, or acceptance)

The prose set is:
- AGENTS.md, README.md, `docs/*.md`;
- `guide/*.md`, `defaults/*.md`, `templates/*.md`;
- `skills/**/*.md`, `agents/*.md`;
- `.sdlc/SDLC.md`, `.sdlc/REVIEW.md`, `.sdlc/PRODUCT.md`;
- `plugins/factory/README.md` and `plugins/factory/{agents,prompts,skills}/**/*.md`;
- the three manifests' `description`.

It leaves out what history holds: `.sdlc/work/`, `.sdlc/retros/` and `.sdlc/DIRECTION.md`, which
retrospectives write as their record. A fixture doc with one of each phrasing proves that each
pattern matches.

R11. `test_no_file_names_a_retired_name`, in the same file, scans the same set with code included.
It fails on any of these: `sdlc\.py['"]?\s+check\b`, `` `check --strict` ``,
`sdlc-factory:verifier`, `\bland-verify\b`, `--task verify\b`, `agents/verifier\.md`,
`prompts/(land-)?verify\.md`.

**The arbiter**

R12. The verifier is the arbiter:
- `git mv` moves its agent file to `plugins/factory/agents/arbiter.md`, with `name: arbiter` and
  `# Arbiter`, run as `sdlc-factory:arbiter`;
- `factory.py`'s `ROLES`, `FIXED_MODELS` (still `sonnet`), `agent --role` choices and `NOTICE` name
  `arbiter`;
- the tasks are `arbitrate` and `land-arbitrate`, and `git mv` moves their prompts to
  `prompts/arbitrate.md` and `prompts/land-arbitrate.md`. The rename covers `TASKS`, `TASK_STEP`,
  `ROUND_PURPOSE`, the mend's `arbitrate` part, and `LAND_STEPS` in both `factory.py` and
  `factory_records.py`;
- the build and land skills, the approver's and reviewers' text, `skills/ship/factory.md`,
  `templates/findings.md`, `guide/review.md` and the factory README say "arbiter";
- `tests/prompts/*verifier*.txt` are regenerated as `*arbiter*.txt`.

`agent --role verifier` and `--task verify` exit 2: `test_the_verifier_role_and_task_are_gone`.
`test_skills.py`'s agent tables (`tools`, `NEVER_RUNS_CHECKS`), `test_prompts.py` and
`test_factory.py` are keyed `arbiter`. `test_modules.py`'s pin fails if the two `LAND_STEPS` differ.

R13. The arbiter's record keeps its names: `reviews/round-N/verified.md`, `VERIFIED`,
`read_verified()`, the `KEPT:`/`DROPPED:` lines, and each round's `verified` field in the readers.
`test_the_arbiter_writes_verified_md` fails if a round's answers land anywhere else.

R14. New records use the new words, and old records still read. A run writes `role: arbiter` to
`costs.jsonl`, `runs/arbiter.sessions`, `arbiter <round>` to `runs/mended`, and `STEP: arbitrate`
or the landing step `arbitrate`. A record from before reads as the arbiter's, for good:
- `role: verifier`, `verifier.sessions` and `verifier <n>`;
- `STEP: verify`;
- a landing step `verify`.

One map does this, `RENAMED = {"verifier": "arbiter", "verify": "arbitrate", "land-verify":
"land-arbitrate"}`, in `factory.py`, with its copy in `factory_records.py` pinned by
`test_every_shared_name_is_the_factorys`. It reads history, so it is not a shim. Each of these
fails without it:
- `test_an_old_verifier_row_counts_as_arbitrate`: the board's `step_samples()`;
- `test_an_old_verify_step_sits_at_arbitrate`: the board's track, built and landing;
- `test_an_old_verifier_mend_counts_for_its_round`: `verdicts` reading `runs/mended`;
- `test_agents_by_role_groups_verifier_with_arbiter`: the retro's *Agents by role and model*, over
  `Sdlc-*` role values and `session_roles()`.

R15. `factory.py start`'s summary says "an arbiter weighs each round's findings" where it said "a
verifier checks each round's changes". `test_skills.py`'s and `test_factory.py`'s asserts on that
text fail otherwise.

R16. `[models] verifier` has no shim. It is an unknown role like any other: `config` warns
`unknown role 'verifier' in models: one of …`, and the arbiter runs on `[models] arbiter` or its
default, `sonnet`. `test_models_verifier_is_an_unknown_role` fails if the old key sets the
arbiter's model. `.sdlc/deprecations.toml` gets no entry.

**The board**

R17. The step tracks label the position `arbitrate`, in both the build track (`TRACK`, `AT`) and
the landing track (`LAND_TRACK`, `LAND_AT`, `LAND_TIMED`). The landing track's `checks` position,
and the `checks` and `recheck` labels, read `acceptance`. The round chip reads
`arbiter: kept N · dropped N`, titled "the arbiter kept / dropped". `test_board.py` asserts each one
on the state JSON and in `board.html`'s text.

R18. The card shows `acceptance: N` where it showed `N check(s)`. Once `build/land-accept.md` holds
an attempt, the card shows `acceptance: N, passed` or `acceptance: N, failed` from its last
attempt's verdict. It never shows a per-check count, which no record holds.
`test_a_card_counts_acceptance_and_its_last_run` fails otherwise.

R19. The gate badge keeps `gate green` / `gate red`, and beside it shows what the gate ran:
`<command>: <summary>, exit <exit>`, for example `./check.sh: 3309 passed, exit 0`.
- `<summary>` is the last line of the recorded output tail that holds a runner's count
  (`\b\d+ (passed|failed)\b`). On red with no such line, it is the tail's last non-empty line. On
  green with none, it is left out.
- `<exit>` is the record's `Exit:` as written (`0`, `timeout`, `didn't run`).
- `hand_gate()` returns `command` and `summary`, and `read_gate_attempts()` reads `Command:` and
  the tail. `factory.py`'s `read_gate_file()` reads the same, pinned by `test_modules.py`'s shared
  cases.
- The page builds the text with `textContent`.

`test_the_gate_badge_names_its_command_and_result` covers a green pytest tail and a red tail with
no count.

**Nits**

R20. Nit 2026-11-19-41: no line of AGENTS.md runs past 100 columns. The factory paragraph's three
long lines are rewrapped like their neighbours. `test_agents_md_fits_100_columns` fails if one runs
over.

R21. Nit 2026-11-19-44: the docstring at `tests/test_metrics.py:496` names the behaviour only, with
no "179 R1". Checked by the grep in *Verification*.

R22. Nit 2026-11-19-52: `tests/test_skills.py`'s two `places` entries lose their `# 183` comments.
Checked by the grep in *Verification*.

**The release**

R23. The change ships with `impact: minor`, as you decided. That matches your earlier calls on
removals, though the guide's table would call it `major`. Its title, which
`templates/changelog.md` renders, says that `sdlc.py check` is now `sdlc.py vet`. REFERENCE.md's
*After an update* says four things: `sdlc.py check` is gone with no alias, a host's CI that calls
it must change to `sdlc.py vet --strict`, setup proposes the new permission rule, and
`[models] verifier` is now `[models] arbiter`. `.sdlc/deprecations.toml` gets no entry, because no
shim is kept to remove.

## Design

**The command.** `cli_check` is renamed to `cli_vet` under `@command("vet", "vet the change
folders against each one's tier and stage", --strict)`. Its body is unchanged. Nothing else in
`sdlc.py` calls it. `READ_ONLY` and `HELP_ORDER` swap the word. `ALLOW_RULES`,
`permissions_status()`, readiness's `permissions` and `setup_nudge()` follow from `READ_ONLY` with
no edit. The skills' bash blocks and rules change by hand, in the exact form `test_skills.py`
matches.

A host's stale `sdlc.py check *` rule is left in place. It allows nothing that exists, and setup
only adds rules.

"Vet" is a word no other part of the plugin uses. "Validation" stays free for milestones and
outcomes, which REFERENCE.md's *Retrospectives* names as the retro's product pass. "Verification"
stays the umbrella.

**The words.** FEATURES.md's *Vocabulary* is where each word is defined, once. Everywhere else, a
retired phrasing is reworded where it stands. The two term tests sit beside the map's tests:
- the phrasings table is `(regex, replacement)` pairs, so a failure says what to write;
- stripping drops `` `…` `` spans and fenced blocks first, so `Sdlc-AfterGate`, `gate=`,
  `verified.md`, `claude plugin validate` and `git rev-parse --verify` never trip it;
- the retired-names table runs over the raw text.

The scripts' printed text is reworded where a person reads it: the board's labels, `start`'s
summary, the landing question, and the `CONFIG_KEYS` comments that `config` shows. Code identifiers
keep their names wherever a record or a trailer holds them: metrics' stop kind `gate`,
`after_gate`, `Sdlc-AfterGate`, `Sdlc-Landed: by=auto`, close's `verify` step, `factory.py check`.

**The arbiter.** `git mv` moves `agents/verifier.md` to `agents/arbiter.md`, and the two prompts to
`arbitrate.md` and `land-arbitrate.md`, so the agent's name, its file and its task match. The
agent's text is reworded, not redesigned: same tools (`Read, Grep, Glob, Bash`), same output shape,
still never runs `checks.md`.

`RENAMED` is applied once at each place a record's word is read:
- `session_roles()`, for the filename stem;
- `step_samples()` and the retro's role grouping, for the row's `role`;
- the `STEP:` and land-step readers, before the `AT`/`LAND_AT` lookup;
- `read_mended()`, for each line.

Writers use only the new words. `agent_name("arbiter")` is `arbiter`. `_models()` is not given the
map, so `[models] verifier` falls to its existing unknown-role warning. A run already in flight
when the plugin updates still works. Its next task is computed from its rounds (`run_state.py`),
which hold only `verified.md`, so it continues as `arbitrate`. Its `runs/mended` lines read through
the map.

**The board.** These are label and data edits in `board.py`'s tables and `board.html`'s `card()`
and `roundRow()`. The record keys stay `checks` and `recheck`, because the landing writes them.
Only the labels change.

For the acceptance count, `card_reading()` adds `accept`: the last attempt's verdict in
`LAND_ACCEPT`, or None.

For the gate badge, `read_gate_attempts()` adds `command` (from `Command: `) and `tail`. The tail
is the indented lines after `Last N lines of its output:`, unindented, already masked by
`placeholders()` when it was written. `hand_gate()` derives `summary` by R19's rule. The record
holds only masked paths, so the badge shows none of this machine's.

**The guide heading.** The guide's slot moves to `#### The gate and the slow gate`, and so does the
prompt in `defaults/SDLC.md`. Most host copies still hold the old heading. `drift` sees that host
block as unchanged since the recorded hash and the default as changed, so it proposes a `refresh`.
Until the host takes it, the host's answer sits under a heading the guide no longer has, and
`doc_units()` reads it after its parent's block. It is still read, never lost.

**Edge cases.**
- A `factory.toml` with both `[models] verifier` and `arbiter` uses `arbiter` and warns about
  `verifier`.
- A gate record from before the `Command:` line shows the badge alone.
- A `land-accept.md` with no readable verdict shows `acceptance: N`.
- `RENAMED` is never applied to `verified.md`, to a reviewer's role or to `[models]`.

## Contracts touched

- **Removing a command with no shim.** AGENTS.md's *Releasing* gives a shim a
  `.sdlc/deprecations.toml` entry. This keeps no shim, so `check` gets no entry, and the file's rule
  is unchanged. The guide's impact table would call a removal `major`. You decided `minor` (R23),
  in line with your earlier calls on removals.
- **A config key dropped: `[models] verifier`.** The intent's constraint said no config key is
  renamed. Your decision overrides it for this one key: it goes with no shim. A host that set it
  gets a warning and the arbiter's default model, `sonnet`. REFERENCE.md's *After an update* says
  so (R23).
- **Files renamed.** The agent and its two prompts move with `git mv` (R12), as you decided. No
  host-facing file is renamed: `checks.md`, `check.sh`, `verified.md`, `gate.md` and the config
  keep their names.
- **Narrow `allowed-tools`.** Each moved command keeps one rule written as it runs. No rule is left
  unused (`test_skills.py`).
- **Read-only allowlist.** `READ_ONLY` still holds only commands that write nothing: `vet` writes
  nothing.
- **Metrics' trailer contract (extend, never redefine).** No key or field is renamed.
  `Sdlc-AfterGate`, `gate=` and `by=auto` keep their names and meanings. Only the prose describing
  them changes.
- **`factory_records.py` holds core's only copies of the factory's parsing, pinned.** `RENAMED`,
  `LAND_STEPS` and the gate-record fields are added to both sides under `factory.py`'s names.
  `test_modules.py` pins them.
- **`factory.py` never imports `sdlc.py`. Core reads the factory's files only.** Unchanged.
- **Agents that judge have no Write. No agent but the builder runs `checks.md`.** The arbiter's
  tools and its never-runs line carry over (`test_no_agent_but_the_builder_runs_checks`).
- **One shape for the shipped docs, and the process docs hold only answers.** The renamed heading
  appears in the guide, the defaults and this repo's answers at once. `sdlc.py record` is rerun so
  `drift` is clean.
- **The board writes nothing and builds every node with `textContent`.** Unchanged. The new text is
  data.
- **Nothing about a project.** The nits remove two citations of change numbers from tests. The new
  tests use neutral fixtures.
- **Windows.** The new tests read with `encoding="utf-8"`, write fixtures with `newline="\n"`, and
  are marked `portable`.
- **Skills' WAIT headings and `READS_CONFIG`.** Untouched.

## Alternatives rejected

- **An alias for `check`.** You ruled it out. Few hosts call it, and skills are what run it.
- **Naming the command `validate`.** That would match `claude plugin validate`, but "validation"
  is reserved for milestones and outcomes. `vet` clashes with nothing.
- **Naming the command `audit`.** You chose `vet`.
- **A shim, or a permanent alias, for `[models] verifier`.** You chose to drop it. A host that set
  it gets a warning naming the roles.
- **Keeping the agent and prompt files under their old names.** The file names would then
  contradict their contents.
- **Keeping the old guide heading.** It would leave "slower check" in the guide. Drift's refresh
  covers hosts.
- **Keeping `verify`/`verifier` in new records and renaming only labels.** The docs and the
  records would then use different words. Writing the new words while reading both costs one map.
- **Renaming `verified.md`.** History holds it, and core reads it through `factory_records.py`.
  You kept it.
- **Renaming the trailer keys (`Sdlc-AfterGate`, `gate=`).** That would redefine a metrics contract
  and split every summary across history.
- **Renaming `[commands] check`, `check.sh`, `checks.md`, `sdlc.py checks`, `sdlc.py accept`,
  `factory.py check` or close's `verify` step.** The intent's constraint rules these out. Each is a
  code name, not prose.
- **A linter that judges meaning.** Nothing can check meaning reliably. A fixed phrasing list fails
  loudly, and review catches the rest.
- **A `tests green` badge.** It claims the gate is only tests. The badge shows the command and its
  result instead.
- **Per-check acceptance counts on the card.** That would need `sdlc.py accept`, which never
  writes, to keep a record. It is a feature the intent didn't ask for.

## Verification

```bash
./check.sh
```
Healthy output: ruff clean, formatted, pytest all passed, `claude plugin validate --strict` passes.

```bash
uv run --group dev pytest -q -n auto tests/test_feature_map.py tests/test_board.py \
  tests/test_factory.py tests/test_skills.py tests/test_modules.py tests/test_readiness.py
uv run --group dev pytest -q -m portable
```
Healthy output: all passed. The two term tests and each R-named test are listed.

```bash
uv run --quiet --script scripts/sdlc.py vet --strict; echo "exit $?"
```
Healthy output: `■ Problems: 0`, `none ✅`, `exit 0`.

```bash
uv run --quiet --script scripts/sdlc.py check; echo "exit $?"
```
Healthy output: argparse's `invalid choice: 'check'`, `exit 2`.

```bash
uv run --quiet --script scripts/sdlc.py drift
```
Healthy output: nothing in `breaking`, `refresh` or `report`.

```bash
rg -n '179 R1' tests/test_metrics.py; rg -n '# 183' tests/test_skills.py; awk 'length > 100' AGENTS.md
```
Healthy output: no output.

```bash
rg -n 'sdlc\.py check\b|\bverifier\b|land-verify' --glob '!.sdlc/{work,retros}/**' \
  --glob '!.sdlc/DIRECTION.md' --glob '!scripts/**' --glob '!plugins/factory/scripts/**' \
  --glob '!tests/**'
```
Healthy output: no output.

Manual check, since no test can show the rendered page. Run `/sdlc:board`. Then:
- A change with a hand gate shows `gate green` and `./check.sh: N passed, exit 0`.
- A factory card's round chip reads `arbiter: kept … · dropped …`.
- Its track reads `arbitrate`, and its landing track reads `acceptance`.

