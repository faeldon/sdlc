I've built change 208: `retro` now reads the host repos you list in `.sdlc/hosts.local`, but only in the plugin's own repo, and it reports counts and fixed words only. Everything is uncommitted, as required. My one full-suite run had 2 failures; I fixed both and reran those tests by name, but I didn't repeat the full run, so the factory gate's run on the build will be the first full one since.

**How it works**
- **The list** (R3): one path per line, with `~`, `#` comments and `!path` exclusions handled. This repo, its worktrees and duplicate lines are counted but not read.
- **Where it reads** (R1, R2): outside the plugin's own repo the `hosts` block says `read only in the plugin's own repo`. With no list it says `no host list`, runs no subprocess and doesn't run `claude plugin list`.
- **Reading a host** (R4, R5): git reads only, reusing `closed_changes()` and `dropped_changes()`. A host that can't be read is counted under `missing`, `not-a-repo`, `no-base` or `failed`. It never fails the retro.
- **Keeping names out** (R7): each host record is cut down to a fixed vocabulary (the plugin's own names, stages, tiers, ways, versions) before anything is added up. A final pass drops any other string and counts it under `read.dropped_names`.
- **The figures** (R6, R8, R12): `read`, `window`, `all`, `busiest`, `versions` and `surface`. Older changes without trailers count as closed but stay out of the medians. Nothing outside `hosts` changes when a list exists.
- **Discovery** (R9): installs the list doesn't name are reported as a count only, or `discovery: "unmeasured"` if `claude plugin list` fails. The failure text is never kept, since it can hold a path.
- **The command** (R10): `sdlc.py hosts` prints each listed repo's state and path, and each unlisted install with the two lines to append. It writes nothing and is in neither `READ_ONLY` nor `ALLOW_RULES`.
- **The report** (R11): a new `## Hosts` section at the end of `templates/retro.md`. Elsewhere it is one line, and an override without `{{hosts}}` renders as before.
- **The insight agents** (R13): every bundle carries `hosts.state`, `hosts.why` and `hosts.read`, plus its pillar's slice from the spec's table.
- **The words** (R14–R16): the retro skill, the insight agent, `AGENTS.md`, `docs/REFERENCE.md`, `docs/CONTRIBUTING.md`, `docs/FEATURES.md`, the module and `cmd_retro()` docstrings, and `.gitignore` (which now lists `.sdlc/hosts.local`).

**Tests added**
`tests/test_retro_hosts.py` has 18 tests, and all 18 failed before the code existed. They prove R1–R13:
- the list format;
- that a host repo never reads a list, and that no list means `unmeasured`;
- that host reads are log and show only, and that an unreadable host is counted, not fatal;
- the exact counts from two fixture hosts;
- that older trailers stay unmeasured rather than zero, and that an empty list shows no zeros;
- that no planted name or path reaches the JSON, the insights or the report, plus the final-pass guard on its own;
- that host figures never move this repo's figures;
- the discovery count;
- the command: it prints and writes nothing, it refuses outside the own repo, and it isn't read-only;
- the report section, and an override template without `{{hosts}}`;
- the insight slices.

I also added `Hosts` to `SECTIONS` in `tests/test_retro.py`.

**Changes to `plan.md`** (written first, after reading the code)
I added a "Where the build departed" section:
- `cmd_hosts()` lives in `retro.py`, with the `sdlc.py` adapter calling it.
- `dropped_changes()` gains `drop_at`, the Drop commit's time, so drops are compared by time like closes. It's additive.
- `read` gains a `repeated` count, so the listed total adds up.
- `dropped_at` is checked against the change stages a drop can record (`sdlc.REACHED`), since `metrics.STAGES` names no `spec` or `plan`.
- R16's spec says `test_feature_map` fails while the command is unmapped, but the feature map lists no script commands at all. I added a `hosts` entry under *The retro's figures* instead.
- A variable called `main` tripped `test_no_git_call_names_main_itself`. Those were the 2 failures in my one full-suite run, which otherwise passed; I renamed it to `checkout` and reran both tests by name.

**Checked by hand**
On this repo with no list, `retro` gives `{'state': 'unmeasured', 'why': 'no host list'}`, `hosts` says how to start a list, and the report's `## Hosts` reads "Not measured: no host list". I didn't run it with a list against your real host repos.

`notes.md`: nothing left in it.

- DECISION: [default] With no `.sdlc/hosts.local`, `sdlc.py hosts` doesn't run discovery, following R9's "discovery runs only when a list exists". It tells you to create the file, which may be empty, and rerun. Going ahead with this unless told otherwise.
  - OPTION: discovery only with a list — follows R9 as written, and nothing calls `claude plugin list` until you've opted in; costs one extra step (create an empty file) the first time
  - OPTION: `hosts` discovers even with no list — easier to start, and the paths only ever go to your terminal; but it bends R9 for the command
  - WHY: R9 is explicit, and an empty file is a cheap opt-in

- UNTESTABLE: R14: the skill's direction-pass and reply wording is judged by eye; `tests/test_skills.py` only confirms the skill runs no new command.
- UNTESTABLE: R15: the insight agent's reading rule is prose, judged by eye.

## Evidence

$ uv run --group dev pytest tests/test_retro_hosts.py -q -n 4   (before the code)
18 failed in 3.43s
exit: 1

$ uv run --group dev pytest tests/test_retro_hosts.py -q -n 4
18 passed in 7.25s
exit: 0

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 208
FAILED tests/test_sdlc.py::test_no_git_call_names_main_itself[retro.py]
FAILED tests/test_sdlc.py::test_the_source_guards_reach_retro_py
2 failed, 3692 passed, 29 skipped in 231.12s (0:03:51)
exit: 1

$ uv run --group dev pytest tests/test_retro_hosts.py "tests/test_sdlc.py::test_no_git_call_names_main_itself" tests/test_sdlc.py::test_the_source_guards_reach_retro_py -q -n 4
22 passed in 41.55s
exit: 0

$ uv run --group dev pytest tests/test_retro_hosts.py tests/test_retro.py tests/test_sdlc.py tests/test_feature_map.py tests/test_skills.py tests/test_nothing_local.py tests/test_defaults.py tests/test_modules.py tests/test_windows.py tests/test_surface.py -q -n 8
1293 passed in 134.26s (0:02:14)
exit: 0

$ uv run --group dev ruff check .
All checks passed!
exit: 0

$ uv run --group dev ruff format --check .
334 files already formatted
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift
{'base': 'manifest', 'version': 2, 'breaking': 0, 'refresh': 0, 'report': 0, 'docs': 3}
exit: 0

$ uv run --quiet --script scripts/sdlc.py hosts
No host list: write one path a line to <path-to-clone>/.sdlc/hosts.local (it may start empty) and rerun to see the installed repos it doesn't name.
exit: 0

$ uv run --quiet --script scripts/sdlc.py retro | python3 -c "import json,sys; print(json.load(sys.stdin)['hosts'])"; uv run --quiet --script scripts/sdlc.py retro --report | sed -n '/^## Hosts/,$p'
{'state': 'unmeasured', 'why': 'no host list'}
## Hosts

Not measured: no host list (.sdlc/hosts.local).
exit: 0
