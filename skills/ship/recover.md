# Ship — how to recover

`preflight`'s `branches` names this file when its `risk` part lists `irreversible` paths: ones
`config`'s `review.irreversible` names.

## Step 4

**How to recover.** A revert of this commit won't undo what those paths reach, so the message
carries a `How to recover:` paragraph after the body, one line per path (or per group of them),
each naming the way back: the command that reverses it, or `fix forward:` and what the follow-up
change would do (for files a host copies at setup, a release without them and `/sdlc:setup` in
each host). For Tier 2, start from `plan.md`'s Rollback section. Show it with the message; Step 5's
question says it was shown.
