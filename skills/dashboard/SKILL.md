---
name: dashboard
description: Open a live board of every open change in this repo — by hand or built by the factory — in the browser, served on localhost by sdlc.py board, each change in its stage's column with its next command, a factory run's rounds, decisions and cost, and a click through to every file in its folder. Use when the human wants to see the pipeline at a glance, or keep it open while changes move. Read-only — it never writes. Not for a one-off answer to what's next (/sdlc:status), and not for acting on a change.
allowed-tools:
  - 'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py board *)'
disable-model-invocation: true
---

# Dashboard — every open change, live

Starts the board and says where it is. The board is a page served on `127.0.0.1` by
`sdlc.py board`, which reads the change folders on every request, the way `/sdlc:status` does, so
it stays current while changes move: a change built by hand shows its stage, artifacts, open
questions, undone notes, findings and the command to run next; one the factory ran on adds its
rounds' verdicts, the verifier's answers, its decisions and what its agents cost.

**Read-only.** The board writes nothing, answers only reads, listens only on this machine, and
serves only the files inside an open change's own folder. This skill starts it and stops there:
it never acts on what the board shows.

## Step 1 — Start it (no confirmation needed)

Run it with `run_in_background`, from wherever the session is, since it serves until stopped:

```bash
uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py board --port 5170
```

Its first output line is JSON: `{"url": …, "serving": true}` once it listens, or `"serving":
"already"` when a board already holds the port, which is then the one to open. A `refusals` line
means something else holds the port: say so, and start it again with another `--port`.

## Step 2 — Say where it is, and stop

Say the URL, `http://127.0.0.1:5170/` unless the port changed, and that the board runs until its
background task is stopped or this session ends. Then stop: no reading of the changes, and no
recommendation, which is `/sdlc:status`'s job.
