---
name: ship
description: Close out a change — run the repo's gate and any build check it configures, review the diff against the repo's review passes, including the change's own folder, then commit the code and the folder together (Stage 5 of the repo's process doc). Use when work on a change to this repo's code, config or tooling is finished and ready to land. It never pushes and never deploys; use /sdlc:status to find the change id first if you don't have it.
argument-hint: "[change id, e.g. 003]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Agent
  - 'Bash(cd *)'
  - 'Bash(git rev-parse *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py preflight *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py findings *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py base *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py ship *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py sync *)'
  - 'Bash(git status *)'
  - 'Bash(git diff *)'
  - 'Bash(git log *)'
  - 'Bash(git commit *)'
  - 'Bash(grep *)'
disable-model-invocation: true
---

# Ship — review and land a change

Stage 5 of the repo's change process. Shipping means: the checks pass, the build check passes when
the diff calls for one, the diff has been reviewed against the repo's review passes, and it lands as
one commit referencing its change folder. It deploys nothing; anything past the commit is the
repo's own path, named in its process doc.

**The review is the point, not the commit.** With one author and one reviewer, this skill is the
only thing standing between a change and `main`. Running the checks and skipping the review passes
defeats it entirely.

## Step 0 — Establish what's shipping (mechanical, no confirmation needed)

```bash
cd "$(git rev-parse --show-toplevel)" && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config && \
git status --short && \
git diff --stat HEAD 2>/dev/null || git diff --cached --stat
```

The fallback is not defensive clutter: `git diff HEAD` fails outright on a repo with no commits,
and the first change a repo ships is exactly when that is true. Then every staged file is the
diff, which is what `--cached` shows. Shipping the change that *adopts* this process is the first
thing anyone does with it, so without the fallback the skill breaks on its own first use. It is two
plain `git diff` calls rather than an `if`, so the skill's allowed tools cover it exactly.

`config` gives the commands Steps 1 and 2 run and the review Step 3 works through. Keep its output
in view; nothing below names the repo's tools any other way. Its `git.base` is the branch a change
lands on, `main` unless the repo's is another; where this skill says `main`, it means that branch.

**Then bring the branch up to date with `git.base`**, before anything is checked or reviewed:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py base <NNN>
```

`/sdlc:close` only fast-forwards, so a gate and a review run on a base `main` has moved past are
spent on code that never lands, and run again after the rebase. This is one of two writes this
skill makes before its WAIT, without asking (the other is Step 3's `findings.md`), because it
touches nothing unless it is clean: a
fast-forward that carries the uncommitted work, or a rebase of the branch's own commits from a
clean tree. `current` needs no mention. `fast-forwarded` or `rebased`: say so, with `behind` (the
commits that came in) and the `undo` line, and carry on. **`refused`: stop here,** before Step 1,
with its `reason`; the person resolves it and runs `/sdlc:ship` again. Never resolve a conflict,
stash, or retry it by hand from this skill.

**`.sdlc/work/` in this skill is `work.dir` from `config`**: this checkout's. The change's folder,
`.sdlc/work/NNN-slug/`, is part of the diff and of the commit: the review reads the artifacts alongside
the code they describe, and `/sdlc:close` takes the folder off `main` once the change lands.

Read `.sdlc/work/NNN-slug/intent.md` and, if Tier 2, `spec.md` — you're about to check the diff against
them.

**Agents' verdicts, when there are any.** A change built by agents (the optional `sdlc-factory`
plugin) has `.sdlc/work/NNN-slug/decision.md`, opening `DECISION: READY` or `DECISION: ESCALATE`, and
its reviews in `.sdlc/work/NNN-slug/reviews/round-<N>/<role>.md`, each opening `VERDICT: PASS` or
`VERDICT: CHANGES`, and the person's calls the agents raised in `.sdlc/work/NNN-slug/decisions.md`
(`- [x]` decided, `- [ ]` assumed). When they exist, read the decision, the highest round's
reviews and the ledger: they are evidence for Step 3, never a substitute for it. A change with
none of them is reviewed exactly as below.

Then everything else this skill looks up about the change, in one call that writes nothing:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py preflight <NNN>
```

Keep its output in view; the steps below read its parts by name, and run none of them again:

- **`undone`**: the unticked `- [ ]` lines in `notes.md`. Step 4 proposes what happens to each.
  `sdlc.py ship` refuses while one is still unticked: a shipped folder isn't read again.
- **`nits`**: the open `[nit]` entries this diff touches, findings an earlier ship approved
  unfixed. Step 4 proposes retiring the ones it fixed or made moot.
- **`closes`**: the issues the intent's `closes:` line names, which Step 4 asks about one by one.
- **`checks`**: the change's acceptance checks, which Step 1 shows and runs.
- **`findings`**: what an earlier run of this review found, from the change's `findings.md`, which
  Step 3 builds on.
- **`risk`**: the paths this diff touches that `config`'s `review.sensitive` and
  `review.irreversible` name, and `deep`, true when a sensitive one is touched. A deep diff gets
  the build check whatever `build_when` says (Step 2) and the fresh-context reviewer (Step 3); an
  irreversible one gets `How to recover:` in its commit (Step 4). Risk never changes the tier: it
  deepens the review, nothing else. The script reads `[review]` from the base branch's checkout,
  so a change can't lighten its own review by editing it.
- **`context`**: the docs the context pass weighs in Step 3.

Empty is the usual answer for the first three. A non-empty `problems` names the part that has one;
a problem in `checks` stops Step 1, and one in `nits` is said in Step 4.

**Check the working tree for unrelated work.** If the diff mixes something else in with this
change, say so plainly and ask whether to commit them separately. Do not silently bundle them — a
large unrelated diff hiding a real change is how review gets skipped. Each path the human chooses
to commit separately is one Step 6 passes to `sdlc.py ship` as `--leave <path>`, since `ship`
stages everything else the checkout has uncommitted.

## Step 1 — Run the checks

Run `commands.check` from `config`, from the repo root. That is the whole step, and it must exit 0.
Don't enumerate what it runs here: the repo defines its gate, and adding a check there is an edit
to the repo, not to this skill.

If `commands.check` is null, the repo has configured no gate. Say so plainly in the report: "no
check configured" is an answer, and a green report with nothing behind it is not. Then run
`sdlc.py check --strict` at least, which audits the change folders:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check --strict
```

**Report the test count the gate printed, if it ran tests,** and what they cover. Say what ran; a
green gate is evidence about what it checks and silence about everything else.

**Then the change's own acceptance checks,** the `## ` sections of its `checks.md`: proof that
only a revert could break, kept out of the suite and rerun here because review fixes and a rebase
may have touched what they check. They are `preflight`'s `checks` part from Step 0, which ran
nothing.

With none listed, say "no acceptance checks" and go on. Otherwise show each check's name and its
command, as listed, and only then run `sdlc.py accept <NNN>`, the same way. It has no rule here on
purpose: an agent may have written those commands, so the person sees them above and answers the
prompt it raises. It runs each from the checkout root and must exit 0. A check fails when its
command exits non-zero, times out, or leaves the working tree changed (`left`). **A failure stops
here, as a failing gate does:** report each failing check's name, `output` and `left`. A problem in
`checks.md` itself, which the `checks` part reports, stops here too.

## Step 2 — If the diff calls for it, run the build check

If `config` sets `commands.build`, run it when any changed path matches `commands.build_when` (a
regex; with none set, always):

```bash
git diff --name-only HEAD | grep -qE '<build_when>' && <build>
```

**On a deep diff (`risk.deep`), run `commands.build` whatever `build_when` says:** a sensitive path
is reason enough. With no build check configured, say so, as below.

The gate is meant to be fast, so it can't tell you everything; the build check is the repo's slower
answer to the questions only a real build can settle. The process doc says what it covers.

Three things to say in the report rather than paper over:

- **Whether it ran at all.** "Not run, the diff touched nothing `build_when` matches" and "no build
  check configured" are fine answers, and better ones than silence.
- **Its results, by name.** Which tests ran and passed, as it reported them.
- **Anything it built that has no tests.** If the repo's policy says what must carry a test, check
  it here; the review's contract pass decides how serious a gap is.

If the build check reports building nothing when the diff clearly changed something it covers, say
so and find out why. Silently building nothing and reporting success is the failure mode here.

## Step 3 — Review the diff — all four passes

Work the review in order: the plugin's guide (`docs.review.guide` from `config`, when it gives
one), then the repo's review doc (`docs.review`), whose blocks stand in for the guide's of the
same heading or lead and add the rest, its own failure classes. Read them if they aren't in
context; when `docs.review`'s `source` is `plugin`, the repo has no review of its own and the
guide stands alone, which is worth saying. Do not skim the diff; read it.

1. **Correctness** — walk the requirements (`spec.md` R1, R2, …, or `intent.md`'s Outcome for
   Tier 1) one at a time and find the code for each. A requirement with no code is a finding. Then
   hunt the failure classes the review names for this repo.
2. **Contract** — every invariant the policy doc (`docs.policy`) declares that the diff comes near.
3. **Cost & simplification** — as the review defines it.
4. **Context** — whether the docs that give a session its context still tell the truth after this
   diff. This pass is the skill's, not the review's, so it runs whatever review the repo has.
   `preflight`'s **`context`** part from Step 0 lists the docs to weigh (`docs.context` from `config`, plus any `CLAUDE.md` above a changed
   path, each with why) and `stale`: their lines naming a path this diff deletes or renames. Read
   each listed doc, then ask of it:

   - Does it now say something false? Every `stale` line is a yes until shown otherwise.
   - Does the diff add something a future session needs and couldn't find quickly by reading the
     code: a command, a convention, an invariant a test now enforces, a part of the architecture
     that takes several files to see?

   The bar is high on purpose. Not a list of files, not a generic practice, not a restatement of
   what the code plainly says: a context doc that grows with every change stops being read. The
   result is either a **proposed edit**, shown as a diff of the doc, or **"no update needed"** with
   one sentence on why. A repo with no context doc at all gets a proposal for one only when the
   diff adds something that meets the bar.

Rank findings **Important**, **Nit** or **Pre-existing**, tag each with its pass, cite its
`path:line` and name its class, as the guide's reporting rules say, and **cap nits at 5** — more
than that means the change is too big, and that's the finding. A Pre-existing finding, a fault in
lines this diff neither adds nor changes and doesn't newly reach, never blocks the commit: it is
proposed as a bug of its own in Step 4.

Weigh each Nit under the rubric in the process (`docs.process.guide`, then `docs.process`), its
section on nits, and give
it a theme, the paths it touches, a cost and a value. One whose value is high was never a nit: rank
it Important. One that costs a design call (L) is an idea for `.sdlc/work/inbox.md`, not a nit. One that
is cheap and worth it (S and med) is the one to suggest fixing now, the "fix a finding first"
answer below. The rest are proposed as `[nit]` entries in `.sdlc/work/inbox.md`.

**On a deep diff, a fresh-context review too,** after your own passes. Spawn the plugin's reviewer
with the `Agent` tool, `subagent_type: "sdlc:reviewer"`, and a prompt holding only the diff
(`git diff HEAD`, the untracked files' paths with it), the change's folder, and the paths of
`docs.review.guide` and `docs.review`: nothing of this session's reasoning, which is what it is
there to be free of. It reads and returns text; it writes nothing. Each finding it returns joins
the file below with a `By: fresh` line. One your own passes confirm, or that you confirm now by
reading its evidence, takes the disposition you'd propose for any finding; one you can't confirm is
proposed `wrong`, with a `Reason:` saying why, for the person to overturn. Never drop one: the
person sees every fresh finding. **When the reviewer can't run** (no `Agent` tool here, or the run
fails), say so in Step 4 and add a line to the file's note, `Fresh review: skipped, <why>`; Step 5
then says so in the question. A deep diff never lands with its fresh review silently missing.

**Then write the findings down,** as `.sdlc/work/NNN-slug/findings.md`, from `templates["findings.md"]`
in `config`: one `## F<n>. [<rank>] [<pass>] <title>` section a finding (`important`, `nit` or
`pre-existing`; `correctness`, `contract`, `cost` or `context`), with its `Evidence:`, `Class:` and
`Disposition:` lines, and `By: fresh` on the fresh reviewer's. This is the one write besides `base` this skill makes before its WAIT, by a
named exception to confirm-before-writing, on every run, a run that stops included: it writes
only the change's own uncommitted folder, decides nothing (the WAIT approves every disposition
in it), and the next run rewrites it. It is how a finding fixed between two runs is counted.

- **When `preflight`'s `findings` part holds an earlier run's,** build on it: keep every id, mark
  one this diff no longer shows `fixed`, never raise again one answered `wrong`, `intentional` or
  `minor` (the person has heard it), and number a new one after the highest id.
- **Each new finding's disposition is the one this skill proposes:** an Important one is `open`,
  until it is fixed; a Nit proposed as a `[nit]` entry, or a Pre-existing one proposed as a bug,
  is `recorded`; a Nit not worth recording is `minor`, with a `Reason:` line.
- **With no findings at all,** the file is the title and note alone, and says nothing to fix.

## Step 4 — Present findings and the draft commit

Read the file back the way the commit will count it:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py findings <NNN>
```

A `problems` entry is a section Step 3 wrote wrong: fix the file and run it again. Open with its
`counts` (`2 important, 1 nit, 1 pre-existing`, or "nothing to fix"), then show each finding with
its id, rank, pass, evidence, class and disposition. **The person answers each one:** a
disposition they change (a finding they say is `wrong`, `intentional` or `minor`, with why) is an
"edit the message" answer, and the file is rewritten and read back before the question is asked
again. Then the exact commit message you propose. Match the repo's style, read from
`git log --oneline -10`. When that style names a change's type (`fix: …`), use the words the
process doc's "Seeds, and the changes they become" gives (`feature`, `fix`, `refactor`…, or the
host's own list there). Absent a clear style: imperative, no Conventional Commits prefix, reads
like a changelog entry, with the change folder named in the body:

```
Let a saved draft be reopened from the list

Add the reopen action to the drafts list, and the test that a second
save keeps one draft. See .sdlc/work/003-reopen-drafts/.
```

When `config` says `archive.ids_from: github`, the change's number is its GitHub issue: end the
body with `Refs #NNN` (the number without its padding), so the commit and the issue that will hold
its artifacts link to each other once pushed. `Refs`, not `Closes`: `/sdlc:close` closes the issue
after it has archived into it, through the `Closes #N` its `Close` commit carries.

End the message with this review's findings as a trailer, a line in its last paragraph (beside
`Refs #NNN` when there is one): the `trailer` line `findings` printed, exactly, which reads
`Sdlc-Findings: important=<n> nit=<n> preexisting=<n> correctness=<n> contract=<n> cost=<n>
context=<n>` and then each disposition's count by pass. Never count it by hand. History keeps it,
so `/sdlc:retro` can count what ship catches and what the person made of it; `/sdlc:close` records
the rest of the change's numbers on its own commit.

If a finding is still `open` (an **Important** one not yet fixed), do not offer to commit. Say what
needs fixing and stop; `findings.md` keeps it for the next run, and `sdlc.py ship` refuses while one
is open.

**Pre-existing findings.** Propose each as the bug entry it becomes, with an id from the
`next-entry` call below: `## [<id>] [bug] <title>`, a line or two on what's wrong and its evidence,
then its `Severity:` (one of the process doc's words, as `/sdlc:bug` asks) and `Paths:` lines, and
a first body line `Found by the review of <NNN-slug>.` No `Introduced by:`: that line is for one
confirmed.

**How to recover**, when `risk.irreversible` names paths: a revert of this commit won't undo what
they reach, so the message carries a `How to recover:` paragraph after the body, one line per path
(or per group of them), each naming the way back: the command that reverses it, or `fix forward:`
and what the follow-up change would do (for files a host copies at setup, a release without them
and `/sdlc:setup` in each host). For Tier 2, start from `plan.md`'s Rollback section. Show it with
the message; Step 5's question says it was shown.

**Agent verdicts.** When Step 0 found `decision.md`, show it under the findings: the decision, its
reasons and its open items, first and plainly when it is `ESCALATE`. Then every decision in
`decisions.md` still unticked: each is an assumption the build rests on that the person hasn't
confirmed, and the approval below confirms it or sends the change back. Then each reviewer's
verdict from the highest round. A `CHANGES` your own passes confirm is a finding like any other; one they
don't is said so, with why. The decision informs the person's approval and never stands in for it.

**Undone items.** For each item Step 0 listed, propose one of two dispositions:

- **carry it forward:** a new `.sdlc/work/inbox.md` seed, with a short title of its own;
- **drop it:** with a one-line reason (done after all, superseded, not worth doing).

There is no third option, such as keeping it as an open question in `intent.md`: a shipped intent
is read no more than its notes. An undone item doesn't block shipping; a known gap can ship once
it's written down somewhere that gets read. Put the dispositions in the commit message, after the
body, as a `Carried forward:` and a `Dropped:` paragraph, one line per item. Leave out a paragraph
that has nothing in it.

**Ids.** Take an id for every entry this ship would add to `.sdlc/work/inbox.md`, the new nits, the
pre-existing bugs, the seeds undone items are carried to and the seeds issues are split off as,
all in one call, `<N>` being how many, so no two share one:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry --count <N>
```

**Nits.** Show the nits proposed, each as the entry it becomes: `## [<id>] [nit] <title>`, a line
or two on what's wrong, then its `Theme:`, `Paths:`, `Cost:`, `Value:` and
`Raised by: <NNN-slug> (<pass>)` lines. Then each nit Step 0 listed that this diff fixed or made
moot, proposed for retirement with a one-line reason, and a `Retired nits:` paragraph in the commit
message after the body, one `- <id>: <reason>` line each. A listed nit the diff doesn't settle
stays, and needs no mention.

**Bugs fixed.** When the intent has a `fixes:` line, name each bug it lists, by id and title from
`.sdlc/work/inbox.md`: `sdlc.py ship` deletes those entries with the commit, and `/sdlc:close` records
each as an `Sdlc-Fixes:` trailer. A listed bug the diff doesn't fix is an **Important** finding:
the line comes out, or the fix goes in.

**Issues it closes.** For each issue `preflight`'s `closes` part listed, show its number and title, with a line on
whether the diff resolves what it asks, and ask, issue by issue, whether this change resolved it.
Only a confirmed one stays on `closes:`, and `/sdlc:close` closes it when the change lands. One the
human says this change didn't resolve is never closed and never dropped: propose a new seed for it,
an `[idea]` or a `[bug]` as the human decides (a bug with its `Severity:`), with an id from the same
`next-entry` call, its `Issue: #N` line, and a first body line `Split from <NNN-slug>:` saying what
is left. Show the `closes:` line as it becomes.

**Context update.** Show the context pass's result under the findings: each proposed edit as a
diff of its doc, or "no update needed" and why. A doc left saying something false is an
**Important** finding, not a nit.

**Release impact.** Propose the change's `impact:` (`major`, `minor`, `patch` or `none`) with
one line of reason, judged from the diff by the process doc's account of releases, if it has one:
what someone holding the previous release has to do differently, can newly do, or merely gets
better. `none` when nothing anyone receives in a release changed. Never infer it from the tier.
Show it under the commit message as `Impact: <part>, because <reason>`.

## Step 5 — WAIT for explicit approval

The script words the question from what Step 4 decided, and reads for itself the sensitive paths
the diff touches and whether it needed `How to recover:`, so neither can be left out. Pass
`--context` when the context pass proposed an edit, `--nits` when nits are added or retired,
`--bugs` when pre-existing findings are filed as bugs, `--fresh-skipped "<why>"` when a deep diff's
fresh review couldn't run, and each issue on `closes:` once, as `--closing N` when this change
resolved it or `--split N` when it is split off as a seed:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py preflight <NNN> --question --context --nits --bugs --fresh-skipped "<why>" --closing <N> --split <K>
```

Ask exactly what it prints. With every clause in, it reads:

> `Commit this, touching sensitive paths <a> and <b>, without the fresh review (<why>), with how to recover it shown, with the context update shown, the nits shown recorded in .sdlc/work/inbox.md, the bugs shown filed in .sdlc/work/inbox.md, closing #N and #M when it lands and splitting #K off as a seed, and .sdlc/work/NNN-<slug>/ stamped shipped, then update its issue? (yes / fix a finding first / edit the message)`

A refusal names an issue left out, given twice, or not on `closes:`: settle it in Step 4, then run
it again. Never word the question by hand.

**Do not commit until the human says go.** Approval is per-invocation, never standing. Never
`git push` — that is not part of this skill under any circumstances. The approval covers the undone
items' dispositions, every finding's disposition in `findings.md`, the nits, the bugs, the context
update, `How to recover:` and the release impact too. A change to one of
them is an "edit the message" answer, and the question is asked again.

## Step 6 — Land it

**The register is the file `config`'s `work.register` names:** `.sdlc/work/inbox.md`. Write
entries there, never into a second file beside it, which would hide every entry the first one
holds.

First, the undone items, exactly as approved:

- **Carried:** append each seed to the register as `## [<id>] [idea] <its title>`, with the id
  Step 4 took for it. If it doesn't exist, `Write` it at that path first from
  `templates["inbox.md"]` in `config`, as it is, then append. Its body says what is left to do and points at
  `.sdlc/work/NNN-slug/notes.md` in this change's commit. Then tick the item in place:
  `- [x] <text> → seed: <id>`.
- **Dropped:** tick it as `- [x] <text> → dropped: <the reason>`.

Then the issues it closes, exactly as approved: take each one this change didn't resolve off the
intent's `closes:` line, and append its seed to the register with its `Issue: #N` line and its
`Split from <NNN-slug>:` line. The seed lands with the change; the `sync` below lets the issue go
from the change's issue, and `/sdlc:close` tells it which seed it stays open as.

Then the nits and the pre-existing bugs, exactly as approved: append each new entry to the
register after its last one, and delete each retired nit, heading to the line before the next
`## `. If it doesn't exist, `Write` it at that path first from `templates["inbox.md"]` in
`config`, as it is, then append. `findings.md` is already as approved: nothing here edits it.

Then make the approved context edits, exactly as shown, in this checkout: they land in the same
commit as the code they describe.

Then set the approved impact on the `impact:` line of `intent.md`'s frontmatter. `sdlc.py ship` refuses without one.

If the change came from a `.sdlc/work/inbox.md` seed and the built thing deviated from the sketch, say
how in `notes.md`, starting it from `templates["notes.md"]` in `config` if the change has none.
`Write` is for those files only, `findings.md` in Step 3, and `.sdlc/work/inbox.md`'s first time: everything else this step
changes already exists, and is edited in place. Never delete the seed's entry by hand: `ship` does.

**When `config`'s `git.attribution` is `false`**, the commit carries the approved message and
nothing more: no `Co-Authored-By:` line naming an agent and no "Generated with" line, whatever the
harness's own guidance says. The host chose that at setup, and a `.claude/settings.local.json` can
still turn the harness's lines back on.

Then, with a `--leave <path>` for each path Step 0's approval set apart:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py ship <NNN>   # stamps, drops the seed, stages
git status --short                                                           # confirm nothing unrelated got staged
git commit -m "<approved message>"
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py sync <NNN>   # the issue, as committed
```

`sync` rewrites the change's issue from the committed folder: `stage: shipped`, the impact, the
commit. "Nothing to sync" is fine. A failure never undoes the commit: report what it printed, and
that `sdlc.py sync <NNN>` can be rerun; `/sdlc:close` renders the issue a last time anyway.

`ship` stamps the folder shipped, deletes the entry the change's `idea:` names and each bug its
`fixes:` names from `.sdlc/work/inbox.md` (saying so when one isn't there), and stages every path the checkout has
uncommitted but the ones left out: the change's code, its folder, `.sdlc/work/inbox.md` when Step 6
edited it, the context docs it edited, and any `.sdlc/last-id` its `new` wrote (the
counter, which reaches `main` this way). It prints each path it staged, and never commits. The
commit message names `NNN-slug`, which is how the commit and its folder find each other.

If `ship` refuses over an undone item, one was missed: give it the disposition the human approved.
If there isn't one, stop and ask; never tick it to get past the refusal. The same goes for the
impact: set the one approved, never one picked to get past it. Two seeds sharing the `idea:`'s
title, or a left-out path that is already staged, is a refusal before anything is written: say
which and stop.

**Read what was staged before committing.** Confirm everything Step 0 flagged as unrelated is still
unstaged. A generated or ignored file in the staged list means the ignore file lost a rule: say
so rather than commit it.

## Step 7 — Report and stop

Report: the commit sha and subject, which checks ran and their results, each acceptance check by
name and its result (or that the change has none), whether the build check ran and what it said, how many findings there were by rank and pass and what became of each, whether the diff was deep and the fresh reviewer ran (and how many of its findings held), the bugs filed by id, which context docs were updated (or
that none needed it), the release impact recorded, each undone
item and where it went (the seed's title, or dropped and why), the nits recorded and retired by
id, and anything else deliberately
deferred. Be explicit that nothing was pushed and nothing was deployed.

Say what ran and what didn't. A report that implies more was verified than was is worse than
useless.

If the change was built in its own worktree (`git rev-parse --git-dir` differs from
`--git-common-dir`), end the report with the next step: **`/sdlc:close NNN`**. It brings the
session back to the main checkout, fast-forwards `main`, mirrors the change to the tracker, takes
its folder off `main` in a commit, removes the worktree and branch, and hands over whatever
cleanup the repo names for a closed change. This skill never merges.

## Out of scope

- `git push`, opening a PR, tagging a release, merging into `main`. Never.
- Deploying anywhere. Whatever path the process doc names for that is separate from this skill.
- Fixing findings. This skill surfaces them; fixing is the human's call and a separate turn.
