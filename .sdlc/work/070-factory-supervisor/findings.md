# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [important] [correctness] A revised spec draft can't carry the person's words

The gate's `revise a requirement` "runs the spec-writer again with their words", and Step 1 runs
it "once more" when the draft lacks something, but `factory.py agent --task spec` sends one fixed
prompt, `Draft spec.md for this change.`, and takes no text: the second draft is written without
what the person asked for or what was missing, so a revise loops on the same draft. Under the old
skill the words went in the `Agent` tool's prompt; moving the agents to `claude -p` behind a bash
rule dropped the only path free text had, on purpose (a person's words in a shell argument can
break the rule match or run `$(...)`), and nothing replaced it.

Evidence: plugins/factory/skills/build/SKILL.md:137, plugins/factory/skills/build/SKILL.md:99, plugins/factory/scripts/factory.py:977
Class: a free-text channel lost moving an agent from a tool call to a command line; the decision answers don't have it, since `decided` reads them from `decisions.md`
Disposition: fixed

## F2. [nit] [correctness] The spec's R5 and R2 say what the code doesn't

R5 promises `factory.py agent … [--to <file>] [--message <text>]`; the code takes `--task`,
`--role` and `--decision` and files each reply by the build's own rules. R2 says the supervisor's
only writes are the spec and stage moves; it also ticks `decisions.md`. `notes.md` records both,
but the spec is what the next reader checks the code against.

Evidence: .sdlc/work/070-factory-supervisor/spec.md:22, .sdlc/work/070-factory-supervisor/spec.md:16
Class: a requirement rewritten in the build and left as it was in the spec
Disposition: fixed
Fix: in spec.md, R5's signature becomes `factory.py agent <NNN> --task <task> [--role <role>] [--decision D<n>]`, its prompt composed from `verdicts`' state and its reply filed by the build's rules (no `--to`); R2's "only writes" adds ticking `decisions.md` with the person's answers.

## F3. [nit] [correctness] One dialog may hold two changes' decisions, and both count it

`decide` asks "one question per pending decision (up to four at once)" without saying they're one
change's: a supervisor with two changes waiting may batch them, and `_supervised()` then keeps the
whole dialog for each change it names, so one stop is counted twice, once on each change.

Evidence: plugins/factory/skills/build/SKILL.md:187, scripts/metrics.py:354
Class: a dialog's attribution resting on a rule the skill doesn't state
Disposition: fixed
Fix: in build/SKILL.md's `decide` bullet, "(up to four at once)" becomes "(up to four at once, all of one change: never two changes' in one dialog)".

## F4. [nit] [cost] The build skill grew from 212 to 285 lines

O5 counts each skill's size. The growth is the spec draft, the background rule and `ready`, each of
which the skill needs to say.

Evidence: plugins/factory/skills/build/SKILL.md:1
Class: a skill's text growing with its job
Disposition: minor
Reason: every added paragraph is a step the supervisor runs; retro's skill-size count will show it, and cutting it is a paydown for when the run has been tried
