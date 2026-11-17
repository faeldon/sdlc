
**Questions resolved from the code:**

- **Is `gate_jobs` read from `.sdlc/factory.toml`, or does the hand gate take one slot of whatever the factory set?** The design reads it, through a pinned copy of `_gate_jobs()` at the base branch (R3). Taking slot 0 alone would make the hand gate fight every factory gate for the slot each one tries first (`gate_slot()` scans from `k = 0`), and wait while others are free.
- **How does the hand gate know the factory is there?** `factory_enabled(home)` (`sdlc.py`), the one answer `sdlc` already keeps. A wrong answer either way writes nothing wrong (Design).
- **Does a give-up count as a failed gate?** No. It is a refusal that writes nothing, since nothing was judged (R4). This follows the intent's "never fails because the factory's slots are busy".

**Left for you to decide:**

- **The policy edit.** `sdlc.py` would read the base branch's `gate_jobs` and lock the factory's slot files, which widens AGENTS.md's "`sdlc` only reads the files a run leaves in a change's folder".
  - Yes: the design stands, and AGENTS.md's factory paragraph gains that clause in this change.
  - No: the fallback is the slot-0-only design. There is no config read and only the lock name is shared, but hand gates wait needlessly when `gate_jobs > 1`.
- **How long a hand gate waits before giving up.** The draft proposes `SLOT_WAIT = GATE_TIMEOUT` (30 minutes).
  - Since each gate ahead is itself capped at 30 minutes, with `gate_jobs = 1` a hand gate gives up only when more than one gate is ahead of it.
  - A shorter limit (say 5 minutes) gives the terminal back sooner but gives up more often while a factory batch lands.
  - "Twice `GATE_TIMEOUT`" covers one queued gate more.
