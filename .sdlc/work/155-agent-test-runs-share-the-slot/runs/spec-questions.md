
I drafted the spec without changing the worktree. Two things in it need your eye before you approve:

- **A policy line in `AGENTS.md` has to change.** It says `factory.py gate` is the one place the factory runs a host's command. The new `check` command also runs it, so the spec rewrites that line to name both, run through one shared function (see Contracts touched).
- **The builder can't cite the gate record for its own build.** The gate only runs after the builder reports, so the record doesn't exist yet when the builder writes its Evidence. The spec has the builder leave the full suite to the gate that runs next. Only reviewers cite the record.

**Questions resolved**
- **How an agent finds the tests "near its change":** it names them itself. The plugin knows nothing about a host's test layout, so the script can't map touched paths to tests.
- **Whether the evidence rules accept a citation of the gate record:** they already do, because `cat` and `head` count as reads. R10 adds a test that pins this; no code change is needed.
- **How an agent learns the `check` command:** today its prompt names no path to `factory.py`. The builder's and the resolver's prompts now carry the full command with the script's absolute path. That path never reaches a committed file, because every filed reply already has machine paths replaced.

**Left for you**
- **Does the builder still run the full suite once before its first report?**
  - My default in the spec: it may, through `check`, but isn't required to, and isn't told to do it just for its Evidence.
  - Relying on the gate entirely saves one full run per build. The cost is that a red gate uses up one of the two fixes allowed per round, and a third red gate stops the change.
  - Requiring one slotted run adds a wait per build but no extra contention for the machine.
- **Two additions beyond the intent's Affected list.** Say if you'd rather drop either.
  - `resolver.md` (R9): the resolver also runs `./check.sh` itself.
  - `scripts/metrics.py` (R11): without it, runs moved into `check` would vanish from `test_runs=`, and the drop you plan to measure would be overstated.
- **`test_runs=` can't tell a full-suite run from a named test run.** So the "drop" it shows is only partly the full suites. A separate count would be its own change.
- **`-n <cores ÷ gate_jobs>` for this repo's gate:** I left it out as this repo's own `check.sh` policy. It could be a seed of its own.
