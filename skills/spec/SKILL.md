---
name: spec
description: Turn an open Tier 2 intent into work/NNN-slug/spec.md — numbered testable requirements, the design, which of the repo's invariants it touches, alternatives rejected, and how it will be verified, in the sections of the repo's spec template (Stage 2 of the repo's process doc). Use after /sdlc:intent has created a Tier 2 change and before building it in plan mode. Skip it entirely for Tier 0 and Tier 1 changes, whose intent.md Approach section already covers the design.
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
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py sync *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py lookup *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py nits *)'
disable-model-invocation: true
---

# Spec — design a Tier 2 change

Stage 2 of the repo's change process. Reads `intent.md` and produces `spec.md`: what will be built,
constrained by the repo's invariants, with the requirements written so they could each be checked.

**The requirements list is the point.** Everything else in the file supports it — it becomes the
checklist for the review's correctness pass and the source of test names. **If you can't write a
numbered, checkable requirement list, the intent isn't understood yet: say so and go back to Stage 1
rather than designing around the fog.**

## Step 0 — Load the change (mechanical, no confirmation needed)

```bash
cd "$(git rev-parse --show-toplevel)" && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py status && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py config
```

**`work/` in this skill is `work.dir` from `config`**: the session's own checkout's. The change's
folder is committed on its branch, so run this from the change's worktree, where `/sdlc:intent`
left the session.

Read `work/NNN-slug/intent.md` in full. Then confirm it's actually Tier 2 — if `tier: 1`, stop and
say so: a Tier 1 change's design belongs in its intent's **Approach** section, and adding a spec to
it is exactly the overhead the tier rule exists to prevent. Offer to promote it to Tier 2 if the
human thinks it has grown.

## Step 1 — Read what constrains it

Before designing anything, read the constraints that already exist. This is the step that makes a
spec worth writing. `config` says where each one is:

- **The policy doc** (`docs.policy`) — the repo's invariants. Every one the change comes near gets a
  line in *Contracts touched*. If `config` says it doesn't exist, say so: the spec then has no
  invariants to design inside, which is worth the human knowing.
- **Everything in `docs.read_before_design`** — the repo's conventions. A design that fights them is
  either wrong or a convention change, and the second is its own decision.
- **The code the change touches.** Read it, and its tests. What it already promises tells you what
  its callers are entitled to assume.
- **The review** (`docs.review`) — the failure classes Stage 5 will look for. If the design comes
  near one, design for it now rather than answering for it at Stage 5.
- **The system itself**, when the design depends on what it actually holds rather than what it's
  assumed to hold. If `docs.explore` names a skill or command for that, use it. A spec written
  against assumptions is how the review's worst findings ship.
- **Open nits** on the paths the design touches: findings earlier ships left unfixed.

  ```bash
  uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py nits --touching <path> <path>
  ```

  Offer the ones of cost `S`, and any whose theme is the change's own, to take in, weighed by the
  rubric in the process doc (`docs.process`). Each one taken becomes a requirement naming its id;
  `/sdlc:ship` retires it once the diff fixes it. Nothing listed is the usual answer. Never take
  one in unasked.

## Step 2 — Resolve the intent's open questions

Work through `intent.md`'s **Open questions** one at a time. For each: answer it, or say explicitly
that it's deferred and why. Ask the human when it's their call rather than a fact you can look up —
and many are facts you *can* look up. Do that first.

Strike the resolved ones in `intent.md` (`~~like this~~`) rather than deleting them — the questions
a change *had* are part of its record, and the strikethrough is what `/sdlc:status` counts.

## Step 3 — Draft and show it

Write the full `spec.md` in the sections of the spec template (`templates["spec.md"]` in `config`);
read it, because each section's prompt says what goes in it, and a repo's own template adds the
sections its domain needs. Whatever the template, two things hold:

- **Requirements** — numbered, each independently checkable. "R4. Saving a draft twice keeps one
  draft, enforced by a test that fails when a second row appears", not "drafts should work".
- **Contracts touched** — for each invariant the change comes near, what it says and how this stays
  inside it. If the design needs one to *change*, say so loudly; that's a policy edit and its own
  decision.

Show it in the conversation.

If the design changes which milestone, project or assignees fit, and `config`'s
`docs.project.fields` turns that field on, list the values it can take and show the intent's new
frontmatter line with the spec. Offer only what it printed, as `/sdlc:intent` does:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py lookup
```

The same goes for what the change serves: when `docs.product` exists and the design changes which
outcomes it serves, or what should move for users, show the intent's new `serves:` line (open ids
from `docs.product.outcomes`, or `none`) and its `**Moves O1:**` lines with the spec, each id with
its `name` beside it, `O1 (Unaided setup)`.

## Step 4 — WAIT for explicit approval

Ask literally:

> `Write this as work/NNN-<slug>/spec.md, advance the change to stage: design and update its issue? (yes / revise a requirement / rethink the design)`

Leave out ` and update its issue` when `config` says `archive.target` is `none`.

**Do not write until the human says go.** Approval is per-invocation, never standing. The yes
covers the issue update too: it is visible to everyone with access to the repo.

## Step 5 — Write it

`Edit` the scaffolded `work/NNN-slug/spec.md` with the approved content, then `Edit` `intent.md`'s
frontmatter: `stage: design`, `updated:` to today. If the design found that this change waits on
another open one, add its id to the frontmatter's `depends_on:` line too, and set any issue field
Step 3 showed. Then:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py check --strict
```

It must exit 0. If it doesn't, fix what it names before reporting. Then mirror the spec and the
new stage to the change's issue:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py sync <NNN>
```

"Nothing to sync" is fine (no tracker, or the change gets its issue at close). A failure never
undoes the spec: report what it printed, and that `sdlc.py sync <NNN>` can be rerun.

## Step 6 — Report and stop

Say the spec is written and that the next step is **plan mode** — start a session in plan mode, let
Claude read the code against this spec, and save the approved plan as `work/NNN-slug/plan.md`.

Do **not** start building in this turn. Do not write code, and do not draft `plan.md` by hand — the
whole value of a plan is that it was produced after reading the code, which is what plan mode does.

## Out of scope

- Implementing anything, including "just the first piece to see if it works".
- Writing `plan.md`. Plan mode produces it; this skill only says so.
- Tier 0 and Tier 1 changes.
- Committing. `/sdlc:ship` does that at Stage 5.
