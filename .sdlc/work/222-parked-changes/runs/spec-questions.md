
**Resolved from the code**
- **Whether a parked change gives up its gate slot.** It does, by construction. A slot is an `flock` on an open descriptor held by the gate's own process (`gate_slot()`, `_try_lock()`), and a busy gate ends its process, so the OS frees the slot. A parked change holds no process, so it holds no slot. The new `SLOT_WAIT` bound (R12) covers the other half: a gate waiting for a slot no longer waits forever.

**Proposed; you can change these**
- **The exit code and the payload.** The code is opt-in: `[park] exit` on the base branch, with no default, and the docs suggest 75 (`EX_TEMPFAIL`). The payload is three optional lines, `SDLC-BUSY-RESOURCE:`, `SDLC-BUSY-HOLDER:` and `SDLC-BUSY-UNTIL:` (R3). A built-in default code would be simpler, but it breaks the constraint that a host never returning busy sees no change.
- **Where the deadline comes from.** The base branch's `[park] deadline`, in minutes (default 60, at most 1440). The host's `UNTIL` sets only the next retry (R4). The alternative, letting the host's answer set the deadline, means a host can keep a change waiting forever.

**Left for you**
- **How autopilot orders parked changes against new ones.** The draft keeps a parked change counted in `in_flight`, so it takes a `parallel` place and a long park holds back the next wave. It retries in its existing order once its `retry` comes. The other choice is to not count it, so new changes start beside it. That puts more changes in flight, and once the park clears there can be more than `parallel` building at once.
- **Whether `decide` gets a clock.** The draft's table records `decide`, `upgrade`, `spec` and `stop` as bounded by the person. Each already sits in Needs you, and autopilot answers `decide` at once. A deadline on `decide` would stop a change no one answered, which only adds a second way to reach Needs you.
- **Parking at landing.** The draft stops the train on a busy landing gate, naming the holder, and never ejects (R13). Under autopilot that holds the batch. Parking the train is a bigger change to `landing.py` (in `[review] sensitive`) and could be a seed of its own.
- **The builder's `check`.** The draft passes the busy code through and prints the holder line (R14), and the builder reports it like any red check. Parking the builder mid-session would mean suspending and resuming its session, which is out of this change's scope.
- **The `AGENTS.md` policy edit.** `verdicts` would read `runs/parked.md` and the clock (see *Contracts touched*). This needs your yes as a policy change.
