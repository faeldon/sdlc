---
name: spec
description: Have the factory's spec-writer agent draft a Tier 2 change's spec.md from its intent, show the draft, and after one approval write it and advance the change to stage design — the factory's stand-in for /sdlc:spec. Use from the change's own worktree, after /sdlc:intent, when the repo has sdlc-factory installed and you want an agent to draft the spec. Not for a Tier 1 change (its intent's Approach is the spec), not for one already past stage plan, and not for writing the spec by hand, which is /sdlc:spec.
argument-hint: "[NNN — the change; this worktree's]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py start *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py write-spec *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage *)'
disable-model-invocation: true
---

# Factory spec — an agent drafts the spec, a person approves it

Stage 2 of the change loop, with the drafting handed to the factory's `spec-writer` agent. The
person still decides: nothing is written until they have read the draft and said yes, exactly as
at `/sdlc:spec`. What changes is who writes the first draft.

The agent writes no file. It returns the spec's text, which `factory.py agent` files whole in the
change's `runs/`, never in `spec.md`; this skill shows it, waits, and has `factory.py write-spec`
copy it into `spec.md` after the yes, byte for byte, so a long draft is never typed out twice.

## Step 0 — The change (mechanical, no confirmation needed)

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py start <NNN> --for spec
```

`config` shows `.sdlc/factory.toml` as resolved: its `factory.models` table sets the agent's model
(`spec-writer = "opus"`) when the repo overrides it. `start` names the change folder and its tier and stage, and every refusal:
not this change's worktree, a Tier 1 change, a stage past `plan`. **If there are refusals, show
them and stop.** For a Tier 1 change, say its intent's Approach stands in for a spec, and that
`/sdlc-factory:build` can start from it.

## Step 1 — Draft it

Start the spec-writer as a session of its own in the change's worktree, with `run_in_background`:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task spec
```

Say `NNN-slug: spec-writer started`, and end the turn. When it exits, read its JSON: `to`, the
draft, `.sdlc/work/NNN-slug/runs/spec-draft.md`; `questions`, the open questions it resolved and
left, `.sdlc/work/NNN-slug/runs/spec-questions.md` (null when it gave none); `preamble`, anything
it wrote before the draft, which is no part of it; or `problem`, a stop to report. Read both files.
Check the draft against `intent.md` before showing it: every `<...>` prompt replaced, requirements
numbered and each checkable, a **Contracts touched** line for each invariant the change comes near.
If one of those is missing, send it back once, to the same spec-writer, which keeps its draft in
context, and say so if the second draft still lacks it:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task spec --recheck
```

Show the person the draft, and the questions the agent resolved and left. A question left for the
person is theirs to answer now, or to leave open in the intent.

## Step 2 — WAIT for explicit approval

Ask literally:

> `Write this as .sdlc/work/NNN-<slug>/spec.md and advance the change to stage: design? (yes / revise a requirement / rethink the design)`

Ask it with `AskUserQuestion`: the text before its parentheses as the question, each answer in
them an option in that order, labelled as written, `header` the skill's name. Only a
chosen `yes` (or `yes, …`), or a yes typed in Other, approves; dismissed, empty, timed out or
refused is a no. If the tool is unavailable or refused, ask the same text, answers in
parentheses, and stop.

**Do not write `spec.md` until the person says yes.** Approval is per-invocation, never standing.
`revise a requirement` is a new draft: the person's words go to the same spec-writer, and the
question is asked again on what it returns. Words never go in a command line: write them at the
end of the change's `decisions.md` (`Write` it with a `# Decisions` heading first when it doesn't
exist) as a ticked line, `- [x] R<n> (person, revise): <their words, as they gave them>`, `<n>`
one past the highest `R` there. It is the one write before this gate, by a named exception to
confirm-before-writing, as ship's `findings.md` is: it writes only the change's own uncommitted
folder, holds only the person's words, and decides nothing. Then, in the background, and back to
Step 1's reading when it exits:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py agent <NNN> --task spec --revise <R1>
```

## Step 3 — Write it

Copy the approved draft into `spec.md` and advance the change:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py write-spec <NNN> && \
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage <NNN> design
```

`write-spec` copies `runs/spec-draft.md` exactly as shown, and refuses, writing nothing, when there
is no draft, the change isn't a Tier 2 at `stage: plan`, or `spec.md` is no longer its scaffold.
**If it refuses, show why and stop.** Then strike the open questions the spec resolved in
`intent.md` with `Edit` (`- ~~Question?~~ Resolved: ...`), as `/sdlc:spec` does.

## Step 4 — Report and stop

Say the spec is written and the change is at `stage: design`. The next step is
**`/sdlc-factory:build NNN`**, where agents plan, build and review it behind one more approval, or
plan mode, to build it by hand. Commit nothing: `/sdlc:ship` makes the change's one commit.

## Out of scope

- Writing code or `plan.md`: that's `/sdlc-factory:build`, or plan mode.
- Tier 1 changes.
- Committing, pushing, or anything outside the change's folder.
