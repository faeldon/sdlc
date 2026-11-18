# Ship — the security review

`preflight`'s `branches` names this file when its `passes` part says `security` applies: the diff
touches a path `config`'s `review.sensitive` names, and the change isn't a factory run, whose own
security reviewer ran.

## Step 3

**A security review too,** beside the fresh-context one. Spawn the plugin's security reviewer with
the `Agent` tool, `subagent_type: "sdlc:security"`, in the same message as `fresh.md`'s
`sdlc:reviewer`, so the two run at once. Its prompt holds what the fresh reviewer's does and
nothing more: the diff (`git diff HEAD`, the untracked files' paths with it), the change's folder,
and the paths of `docs.review.guide`, `docs.review` and `docs.policy`. Nothing of this session's
reasoning goes in. It reads, returns text and writes nothing. Each finding it returns joins the
file with a `By: ship-security` line. Treat it as you treat a fresh finding: confirm it by reading
its evidence and give it the disposition you'd propose, or propose it `wrong`, with a `Reason:`, for
the person to overturn. Never drop one.

The note says `Security review: ran`. **When the reviewer can't run** (no `Agent` tool here, or the
run fails), it says `Security review: skipped, <why>`, said in Step 4 too. The script reads that
line: the question names a skip, and `sdlc.py ship` refuses a diff this applies to whose note says
neither.
