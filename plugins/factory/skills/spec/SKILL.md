---
name: spec
description: Have the factory's spec-writer agent draft a Tier 2 change's spec.md from its intent, show the draft, and after one approval write it and advance the change to stage design — the factory's stand-in for /sdlc:spec. Use from the change's own worktree, after /sdlc:intent, when the repo has sdlc-factory installed and you want an agent to draft the spec. Not for a Tier 1 change (its intent's Approach is the spec), not for one already past stage plan, and not for writing the spec by hand, which is /sdlc:spec.
argument-hint: "[NNN — the change; this worktree's]"
allowed-tools:
  - Read
  - Edit
  - Agent
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py config *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py start *)'
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage *)'
disable-model-invocation: true
---

# Factory spec — an agent drafts the spec, a person approves it

Stage 2 of the change loop, with the drafting handed to the factory's `spec-writer` agent. The
person still decides: nothing is written until they have read the draft and said yes, exactly as
at `/sdlc:spec`. What changes is who writes the first draft.

The agent writes no file. It returns the spec's text; this skill shows it, waits, and writes it.

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

Spawn the agent with the `Agent` tool, `subagent_type: "sdlc-factory:spec-writer"`, its model
from `factory.models` if `config` set one, and this prompt:

> `Change folder: <folder>. Worktree: <the worktree root>. Draft spec.md for this change.`

It returns the complete `spec.md` (frontmatter as scaffolded) and, after a `---` line, the open
questions it resolved and those it left. Read the draft yourself against `intent.md` before showing
it: every `<...>` prompt replaced, requirements numbered and each checkable, a **Contracts
touched** line for each invariant the change comes near. Send it back to the agent once if one of
those is missing; say so if the second draft still lacks it.

Show the person the draft, and the questions the agent resolved and left. A question left for the
person is theirs to answer now, or to leave open in the intent.

## Step 2 — WAIT for explicit approval

Ask literally:

> `Write this as .sdlc/work/NNN-<slug>/spec.md and advance the change to stage: design? (yes / revise a requirement / rethink the design)`

**Do not write until the person says yes.** Approval is per-invocation, never standing. A revision
is a new draft: send it back to the agent with the person's words, show it, and ask again.

## Step 3 — Write it

`Edit` the scaffolded `.sdlc/work/NNN-slug/spec.md` with the approved draft, exactly as shown. Strike
the open questions the spec resolved in `intent.md` (`- ~~Question?~~ Resolved: ...`), as
`/sdlc:spec` does. Then:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/factory.py stage <NNN> design
```

## Step 4 — Report and stop

Say the spec is written and the change is at `stage: design`. The next step is
**`/sdlc-factory:build NNN`**, where agents plan, build and review it behind one more approval, or
plan mode, to build it by hand. Commit nothing: `/sdlc:ship` makes the change's one commit.

## Out of scope

- Writing code or `plan.md`: that's `/sdlc-factory:build`, or plan mode.
- Tier 1 changes.
- Committing, pushing, or anything outside the change's folder.
