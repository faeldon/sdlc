# Ship — the UI and UX reviews

`preflight`'s `branches` names this file when its `passes` part says `ui` applies. That is when the
base branch's `.sdlc/factory.toml` has a complete `[ui]`, the diff touches its `paths`, and the
change isn't a factory run, whose own reviewers ran.

## Step 3

**With `passes.ui.shots` listed,** spawn the plugin's two page reviewers with the `Agent` tool:
`subagent_type: "sdlc:ui"` and `subagent_type: "sdlc:ux"`. Spawn them in one message, the fresh
review's too when `fresh.md` applies.

Each prompt holds only:

- the diff;
- the change's folder;
- the paths of `docs.review.guide` and `docs.review`;
- the screenshots in `passes.ui.shots`;
- the changed paths under `[ui] paths`.

Nothing of this session's reasoning goes in. Ship never takes a screenshot itself. These are the
ones `factory.py shots` left, and `preflight` lists a set only when it is newer than every changed
page.

Each finding returned joins the file with `By: ship-ui` or `By: ship-ux`. Treat it as you treat a
fresh finding: confirm it, or propose it `wrong` with a `Reason:`. Never drop one. Then the note
says `UI review: ran` and `UX review: ran`. A reviewer that can't run gets `skipped, <why>` on its
line instead.

**With no shots,** neither reviewer runs. The note says `UI review: skipped, <why>` and `UX review:
skipped, <why>`, with `passes.ui.why` as the why, and Step 4 says so too. With `sdlc-factory`
enabled, the why names the command that takes them, `factory.py shots NNN --round 1 --role ui`:
the person runs it and reruns ship, and ship never runs it. A skip is no stop: the question names
it, and `sdlc.py ship` stamps the change. It refuses only a note that says neither.
