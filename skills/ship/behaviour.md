# Ship — the behaviour check

`preflight`'s `branches` names this file when its `passes` part says `behaviour` applies: a Tier 2
change with a filled `spec.md`, not a factory run, whose own behaviour reviewer ran.

## Step 3

**Run the spec's path end to end, as a person would.** This is your own work, not an agent's. From
the spec's requirements and its `## Verification`, name the path: the commands a person would run
and what each requirement says they'd see. Leave out `commands.check`, which Step 1 already ran.
Leave out every command in the change's `checks.md`: Step 1 ran those as the acceptance checks, so
never run one here. Show the list first.

Then take `git status --short`, run each command in turn, and take `git status --short` again.
Show each command before it runs. No rule in this skill covers these commands, on purpose: the
person answers each one's prompt, as they do for the acceptance checks.

Each failure against a requirement is an **Important** `[correctness]` finding, `open` or `fix` as
any other, with `By: ship-behaviour`. Its `Evidence:` is the command and what it printed, and its
`Class:` is what the requirement says should happen.

The note says `Behaviour check: ran`, and the file ends with an `## Evidence` section. Each command
there is a `$ ` line, then the tail of what it printed, then `exit: <n>`. `sdlc.py findings` reads
that section as evidence, never as a finding, and reports a command without its `exit:`.

When the spec names no path to run, or the person declines a command's prompt, the note says
`Behaviour check: skipped, <why>`, said in Step 4 too.

## Step 4

**What the path left behind.** Compare the two `git status --short` lists. Name each path the
second shows that the first didn't, in the evidence and here. Propose removing it, or setting it
apart: Step 6 passes a path set apart to `sdlc.py ship` as `--leave <path>`. Nothing the check wrote
is committed unasked.
