# Ship — the fresh-context review

`preflight`'s `branches` names this file when its `risk` part says `deep`: the diff touches a path
`config`'s `review.sensitive` names.

## Step 3

**A fresh-context review too,** after your own passes. Spawn the plugin's reviewer with the `Agent`
tool, `subagent_type: "sdlc:reviewer"`, and a prompt holding only the diff (`git diff HEAD`, the
untracked files' paths with it), the change's folder, and the paths of `docs.review.guide` and
`docs.review`: nothing of this session's reasoning, which is what it is there to be free of. It
reads and returns text; it writes nothing. Each finding it returns joins the file below with a
`By: fresh` line. One your own passes confirm, or that you confirm now by reading its evidence,
takes the disposition you'd propose for any finding; one you can't confirm is proposed `wrong`,
with a `Reason:` saying why, for the person to overturn. Never drop one: the person sees every
fresh finding. On a deep diff the file's note always says which happened: `Fresh review: ran`, or,
**when the reviewer can't run** (no `Agent` tool here, or the run fails), `Fresh review: skipped,
<why>`, said in Step 4 too. The script reads that line: the question names a skip, and `sdlc.py
ship` refuses a deep diff whose note says neither, so it never lands with its fresh review
silently missing.
