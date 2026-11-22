
Open questions resolved:

- **Does `cmd_answer` get a lock, or only a comment?** A docstring, plus a test that pins the rule (R5). The code settles it:
  - Only `decisions` and `answer` write the ledger during a run.
  - The loop answers a change's lines one at a time (autopilot.py:555).
  - The only commands it starts together are a review's roles, which never write the ledger.
  - A lock would also miss the one writer outside the loop, `/sdlc-factory:decide`'s Edit-tool edit.

  If you'd rather have a lock anyway, it costs a new state file in the git common dir, shared by `decisions` and `answer`. The plan would grow by one step and R5's test would stay.
- **Is `recorded_closes()`' reread worth caching?** No. It is accepted as a stated cost and pinned (R7). Each process calls it once, so a cache inside the process saves nothing, and a cache across processes would be a new state file.
- **Which loop path does the end-to-end test drive?** One seed, landed cleanly, with one decision really answered by `answer --by autopilot` on the way (R1). Holds and parks are decided in the loop's own process and are already covered there, and the things only a real subprocess run can show are all on the clean path.

Left for the person:

- **The bound on the end-to-end test's run time.** It is asked under Boundaries before the test grows past one seed. If its measured time in `./check.sh` is too long for you, the other choice is a `slow` mark that `check.sh` still runs but that can be deselected locally.
