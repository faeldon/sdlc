I've built all 15 requirements of 209. Everything is uncommitted, and the full gate passes (3693 passed, 29 skipped). Nothing was sent to GitHub during the build: every test runs against the fake `gh`.

**What it does now**
- **New `sdlc.py upstream` command.** It reads the plugin's repo from its own manifest, never from an argument or the host. In the plugin's own repo, or with no `gh` or no login, it says it can't file and why.
- **`--render`** builds the issue only from the seven allowed sections of the input file (in the git common dir). Any other section is dropped and listed in `left_out`. Before anything else, every field goes through one cutter, `_cut_host()`:
  - It replaces URLs, paths, `Sdlc-*` values, commit SHAs, `#N` refs and the host's names (folder, remotes, branches, changes, entries, git user, config values) with placeholders.
  - If a name is still there afterwards, the field is left out with `*Left out: it named the host.*`.
  - Output keeps its last 40 lines. Diagnostics give versions, scopes and config key names, never values.
  - The key is a hash of the title and body.
- **`--send --key`** refuses a key the input no longer renders to. Under the main lock it records `sending` before `gh` runs and `filed` after, so a rerun never files twice. After a stopped send it searches your own issues for the marker before filing again. Without `gh` it files nothing and exits 0.
- **The GitHub tracker** has the upstream calls. `gh` and `github.com` have to stay out of the core script, so the URL parsing lives there too. The new issue is created with `--repo`, `--title` and `--body-file` only.
- **`intake`** now flags `from_host` on issues that open with `<!-- sdlc:host-bug:`.
- **Skills and docs.** `/sdlc:bug` asks, in a host only, whether the bug is the host's or the plugin's. It renders and shows the body, then asks `File this bug publicly on <owner/name> as <login>? Anyone can read it. (yes / edit it / no)` and sends only on yes. `/sdlc:triage` writes `Origin: host` for flagged issues. REFERENCE.md, README, FEATURES.md and AGENTS.md are updated. A new acceptance check in `checks.md` covers the doc lines, which no test reads.

**Tests added**
- `tests/test_upstream.py`, 14 tests. The main one fills a fake host with distinct sentinel names and fails if any reaches the rendered title or body.
- One `intake` test in `tests/test_archive.py`, next to the other intake tests (the plan said `test_intake.py`).
- Two tests on the bug skill's text in `tests/test_skills.py`.
- The fake `gh` in `tests/conftest.py` now answers `auth token`, `api user` and `issue list --state all`.

**Changes to `plan.md`:** I filled it in, moved the intake test as above, recorded the split-out config read (`_config_data()`), and added an "As built" section for the calls below.

**Where I went beyond or short of the spec**
- **File contents in the output can't be caught.** R4 asks that file contents never reach the body, but the cutter only knows the names it can see. Contents in a separate section are dropped; contents pasted into the output would get through. The protection there is that you see the exact body before the yes. Accepting this gap, or deciding how to close it, is up to you.
- **The two policy edits the spec left to you** (another way to load the GitHub tracker, and a sixth write before a WAIT) are written into AGENTS.md. I recorded them as defaults below rather than deciding them silently.
- **`notes.md`:** nothing left there.

- UNTESTABLE: none

- DECISION: [default] Keep file contents out of the body only by dropping sections that aren't allowed and by showing the body before the yes, since the cutter can't recognise them inside the output? Going ahead with that unless told otherwise.
  - OPTION: allowlist plus preview — no scanning of tracked files; contents pasted into the output can still be sent
  - OPTION: also leave out output lines that match the host's tracked files' lines — catches more; slow on a big repo, and leaves out common lines
  - WHY: R4's sentinel test can't place unknown contents, and the WAIT shows exactly what leaves
- DECISION: [default] List only the config keys the plugin knows, and count the rest without naming them ("and N not the plugin's")? Going ahead with that unless told otherwise.
  - OPTION: known keys named, others counted — nothing the host invented leaves it; the plugin can't see which unknown key
  - OPTION: every key named — matches R5's wording; a key the host made up could name something
  - WHY: the intent's "allowlist, not a scrubber" constraint
- DECISION: [default] Don't cut names every host has (the default base branch, `master`, `origin`, and config values equal to the plugin's defaults), and keep relative paths that exist in the plugin's own copy, such as `scripts/sdlc.py`? Going ahead with that unless told otherwise.
  - OPTION: exempt common names and the plugin's paths — readable bodies; these say nothing about the host
  - OPTION: cut every config value and every relative path — closer to R6's letter; "the main checkout" reads "the <config> checkout"
  - WHY: they identify no host, and cutting them makes the plugin's own messages unreadable
- DECISION: [default] Word AGENTS.md's tracker rule as "loaded only when `archive.target` names it, or, the GitHub one alone, by `upstream`", and count the input file as a sixth write before a WAIT? Going ahead with that wording unless told otherwise.
  - OPTION: the edits as written — they say what the code now does
  - OPTION: other wording of your choice — the spec left the policy to you
  - WHY: the spec's *Contracts touched* names both as the person's call, and R15 asks for the edits

## Evidence

$ uv run --quiet --script <path-to-clone>/plugins/factory/scripts/factory.py check 209
All checks passed!
3693 passed, 29 skipped in 354.13s (0:05:54)
✔ Validation passed
✔ Validation passed
exit: 0

$ uv run --group dev pytest -q tests/test_upstream.py tests/test_archive.py::test_intake_flags_an_issue_from_a_host tests/test_skills.py::test_bug_asks_which_kind_before_filing_upstream tests/test_skills.py::test_bug_shows_the_upstream_body_before_its_wait
17 passed in 12.83s
exit: 0

$ uv run --group dev pytest -q -m portable tests/test_upstream.py
5 passed, 9 deselected in 25.45s
exit: 0

$ uv run --group dev pytest -q tests/test_upstream.py   (first run, before any code)
14 failed in 10.61s
exit: 1

$ uv run --group dev pytest -q tests/test_archive.py -k from_a_host   (before the intake code)
1 failed, 174 deselected in 0.67s
exit: 1

$ uv run --group dev pytest -q tests/test_skills.py -k upstream   (before the skill edit)
2 failed, 447 deselected in 0.27s
exit: 1

$ sh -c "<checks.md's block>"
exit: 0
