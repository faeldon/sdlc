# Ship — the docs review

`preflight`'s `branches` names this file when its `passes` part says `docs` applies: the diff
touches a doc the base branch's `[docs] context` or `[docs] reviewed` lists, a path one of them
names, a path with a `CLAUDE.md` or `AGENTS.md` above it, or any path outside `tests/`; and the
change isn't a factory run, whose own docs reviewer ran.

## Step 3

**A docs review too.** Spawn the plugin's docs reviewer with the `Agent` tool, `subagent_type:
"sdlc:docs"`, in the same message as any other reviewer this step spawns, so they run at once. Its
prompt holds the diff (`git diff HEAD`, the untracked files' paths with it), the change's folder,
`preflight`'s `context` part (its `docs` and `stale` lines), and the docs `docs.reviewed` names
in `config`. Nothing of this session's reasoning goes in. It reads, returns text and writes
nothing.

With it running, pass 4 leaves "does it now say something false" to it, and asks only the other
two questions. Each finding it returns joins the file with a `By: ship-docs` line, in the
`context` pass. Treat it as you treat a fresh finding: confirm it by reading its evidence and give
it the disposition you'd propose, or propose it `wrong`, with a `Reason:`, for the person to
overturn. Never drop one. An edit it proposes to a context doc is shown with the context pass's
own, under **Context update** in Step 4.

The note says `Docs review: ran`. **When the reviewer can't run** (no `Agent` tool here, or the run
fails), it says `Docs review: skipped, <why>`, said in Step 4 too, and pass 4 asks all three of its
questions itself. The script reads that line: the question names a skip, and `sdlc.py ship`
refuses, when the change has a `findings.md`, a diff this applies to whose note says neither.
