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
  - 'Bash(cd *)'
  - 'Bash(git rev-parse *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py undone *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py nits *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py base *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py checks *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py context *)'
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
spent on code that never lands, and run again after the rebase. This is the one write this skill
makes before its WAIT, without asking, because it touches nothing unless it is clean: a
fast-forward that carries the uncommitted work, or a rebase of the branch's own commits from a
clean tree. `current` needs no mention. `fast-forwarded` or `rebased`: say so, with `behind` (the
commits that came in) and the `undo` line, and carry on. **`refused`: stop here,** before Step 1,
with its `reason`; the person resolves it and runs `/sdlc:ship` again. Never resolve a conflict,
stash, or retry it by hand from this skill.

**`work/` in this skill is `work.dir` from `config`**: this checkout's. The change's folder,
`work/NNN-slug/`, is part of the diff and of the commit: the review reads the artifacts alongside
the code they describe, and `/sdlc:close` takes the folder off `main` once the change lands.

Read `work/NNN-slug/intent.md` and, if Tier 2, `spec.md` — you're about to check the diff against
them.

**Agents' verdicts, when there are any.** A change built by agents (the optional `sdlc-factory`
plugin) has `work/NNN-slug/decision.md`, opening `DECISION: READY` or `DECISION: ESCALATE`, and
its reviews in `work/NNN-slug/reviews/round-<N>/<role>.md`, each opening `VERDICT: PASS` or
`VERDICT: CHANGES`, and the person's calls the agents raised in `work/NNN-slug/decisions.md`
(`- [x]` decided, `- [ ]` assumed). When they exist, read the decision, the highest round's
reviews and the ledger: they are evidence for Step 3, never a substitute for it. A change with
none of them is reviewed exactly as below.

Then list what the change's notes left undone:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py undone <NNN>
```

Each item is an unticked `- [ ]` line in `notes.md`. Step 4 proposes what happens to each one.
`sdlc.py ship` refuses while one is still unticked, because a shipped folder isn't read again,
and an item left there is lost.

Then list the open nits this change's diff touches, from `work/nits.md`:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py nits --change <NNN>
```

Each is a finding an earlier ship approved unfixed. Step 4 proposes retiring the ones this diff
fixed or made moot. None listed, or no `work/nits.md`, is the usual answer.

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
may have touched what they check. List them first; this runs nothing:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py checks <NNN>
```

With none listed, say "no acceptance checks" and go on. Otherwise show each check's name and its
command, as listed, and only then run `sdlc.py accept <NNN>`, the same way. It has no rule here on
purpose: an agent may have written those commands, so the person sees them above and answers the
prompt it raises. It runs each from the checkout root and must exit 0. A check fails when its
command exits non-zero, times out, or leaves the working tree changed (`left`). **A failure stops
here, as a failing gate does:** report each failing check's name, `output` and `left`. A problem in
`checks.md` itself, which `checks` reports, stops here too.

## Step 2 — If the diff calls for it, run the build check

If `config` sets `commands.build`, run it when any changed path matches `commands.build_when` (a
regex; with none set, always):

```bash
git diff --name-only HEAD | grep -qE '<build_when>' && <build>
```

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

Work the review (`docs.review` from `config`) in order. Read it if it isn't in context; when its
`source` is `plugin`, the repo has no review of its own and the plugin's default stands in, which
is worth saying. Do not skim the diff; read it.

1. **Correctness** — walk the requirements (`spec.md` R1, R2, …, or `intent.md`'s Outcome for
   Tier 1) one at a time and find the code for each. A requirement with no code is a finding. Then
   hunt the failure classes the review names for this repo.
2. **Contract** — every invariant the policy doc (`docs.policy`) declares that the diff comes near.
3. **Cost & simplification** — as the review defines it.
4. **Context** — whether the docs that give a session its context still tell the truth after this
   diff. This pass is the skill's, not the review's, so it runs whatever review the repo has:

   ```bash
   uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py context
   ```

   It lists the docs to weigh (`docs.context` from `config`, plus any `CLAUDE.md` above a changed
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

Rank findings **Important** or **Nit**, tag each with its pass, and **cap nits at 5** — more than
that means the change is too big, and that's the finding.

Weigh each Nit under the rubric in the process doc (`docs.process`), its section on nits, and give
it a theme, the paths it touches, a cost and a value. One whose value is high was never a nit: rank
it Important. One that costs a design call (L) is a seed for `work/inbox.md`, not a nit. One that
is cheap and worth it (S and med) is the one to suggest fixing now, the "fix a finding first"
answer below. The rest are proposed for `work/nits.md`.

## Step 4 — Present findings and the draft commit

Show the findings, then the exact commit message you propose. Match the repo's style, read from
`git log --oneline -10`. Absent a clear one: imperative, no Conventional Commits prefix, reads like a
changelog entry, with the change folder named in the body:

```
Let a saved draft be reopened from the list

Add the reopen action to the drafts list, and the test that a second
save keeps one draft. See work/003-reopen-drafts/.
```

When `config` says `archive.ids_from: github`, the change's number is its GitHub issue: end the
body with `Refs #NNN` (the number without its padding), so the commit and the issue that will hold
its artifacts link to each other once pushed. `Refs`, not `Closes`: `/sdlc:close` closes the issue
after it has archived into it, through the `Closes #N` its `Close` commit carries.

End the message with this review's findings as a trailer, a line in its last paragraph (beside
`Refs #NNN` when there is one), counts only:
`Sdlc-Findings: important=<n> nit=<n> correctness=<n> contract=<n> cost=<n> context=<n>`, each
pass's count of findings, Important and Nit together. History keeps it, so `/sdlc:retro` can count
what ship catches; `/sdlc:close` records the rest of the change's numbers on its own commit.

If there are **Important** findings, do not offer to commit. Say what needs fixing and stop.

**Agent verdicts.** When Step 0 found `decision.md`, show it under the findings: the decision, its
reasons and its open items, first and plainly when it is `ESCALATE`. Then every decision in
`decisions.md` still unticked: each is an assumption the build rests on that the person hasn't
confirmed, and the approval below confirms it or sends the change back. Then each reviewer's
verdict from the highest round. A `CHANGES` your own passes confirm is a finding like any other; one they
don't is said so, with why. The decision informs the person's approval and never stands in for it.

**Undone items.** For each item Step 0 listed, propose one of two dispositions:

- **carry it forward:** a new `work/inbox.md` seed, with a short title of its own;
- **drop it:** with a one-line reason (done after all, superseded, not worth doing).

There is no third option, such as keeping it as an open question in `intent.md`: a shipped intent
is read no more than its notes. An undone item doesn't block shipping; a known gap can ship once
it's written down somewhere that gets read. Put the dispositions in the commit message, after the
body, as a `Carried forward:` and a `Dropped:` paragraph, one line per item. Leave out a paragraph
that has nothing in it.

**Nits.** Show the nits proposed for `work/nits.md`, each as the entry it becomes: `## <NNN>-<n>
[<theme>] <title>`, numbered from 1 for this change, with its `raised`, `paths` and `cost`/`value`
lines. Then each nit Step 0 listed that this diff fixed or made moot, proposed for retirement with
a one-line reason, and a `Retired nits:` paragraph in the commit message after the body, one
`- <id>: <reason>` line each. A listed nit the diff doesn't settle stays, and needs no mention.

**Context update.** Show the context pass's result under the findings: each proposed edit as a
diff of its doc, or "no update needed" and why. A doc left saying something false is an
**Important** finding, not a nit.

**Release impact.** Propose the change's `impact:` (`major`, `minor`, `patch` or `none`) with
one line of reason, judged from the diff by the process doc's account of releases, if it has one:
what someone holding the previous release has to do differently, can newly do, or merely gets
better. `none` when nothing anyone receives in a release changed. Never infer it from the tier.
Show it under the commit message as `Impact: <part>, because <reason>`.

## Step 5 — WAIT for explicit approval

Ask literally:

> `Commit this, with the context update shown, the nits shown recorded in work/nits.md, and work/NNN-<slug>/ stamped shipped, then update its issue? (yes / fix a finding first / edit the message)`

Leave out `, with the context update shown` when the context pass proposed none, `, the nits shown
recorded in work/nits.md` when there are none to add or retire, and `, then update its issue` when
`config` says `archive.target` is `none`.

**Do not commit until the human says go.** Approval is per-invocation, never standing. Never
`git push` — that is not part of this skill under any circumstances. The approval covers the undone
items' dispositions, the nits, the context update and the release impact too. A change to one of
them is an "edit the message" answer, and the question is asked again.

## Step 6 — Land it

First, the undone items, exactly as approved:

- **Carried:** take an id for each seed carried, all in one call, `<N>` being how many:

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py next-entry --count <N>
  ```

  Then append each seed to `work/inbox.md` as `## [<id>] [seed] <its title>`. If there's no
  `work/inbox.md`, `Write` it first from `templates["inbox.md"]` in `config`, as it is, then
  append. Its body says what is left to do and points at `work/NNN-slug/notes.md` in this
  change's commit. Then tick the item in place: `- [x] <text> → seed: <id>`.
- **Dropped:** tick it as `- [x] <text> → dropped: <the reason>`.

Then the nits, exactly as approved: append each new entry to `work/nits.md` after its last one,
and delete each retired entry, heading to the line before the next `## `. If there's no
`work/nits.md`, `Write` it first from `templates["nits.md"]` in `config`, as it is, then append.

Then make the approved context edits, exactly as shown, in this checkout: they land in the same
commit as the code they describe.

Then set the approved impact on the `impact:` line of `intent.md`'s frontmatter. `sdlc.py ship` refuses without one.

If the change came from a `work/inbox.md` seed and the built thing deviated from the sketch, say
how in `notes.md`, starting it from `templates["notes.md"]` in `config` if the change has none.
`Write` is for those files only, and `work/nits.md`'s first time: everything else this step
changes already exists, and is edited in place. Never delete the seed's entry by hand: `ship` does.

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

`ship` stamps the folder shipped, deletes the entry the change's `idea:` names from
`work/inbox.md` (saying so when there is none), and stages every path the checkout has
uncommitted but the ones left out: the change's code, its folder, `work/inbox.md` and
`work/nits.md` when Step 6 edited them, the context docs it edited, and any `.sdlc/last-id` its `new` wrote (the
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
name and its result (or that the change has none), whether the build check ran and what it said, how many findings there were by pass, which context docs were updated (or
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
