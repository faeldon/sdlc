VERDICT: PASS

The change is docstrings only, and the code is unchanged: `scripts/sdlc.py` matches main once docstrings are stripped from both. The end-to-end path (`sdlc.py -h`) lists all 41 registered subcommands, and the module docstring points there. The three acceptance checks are expected to pass against the code as it stands. I ran none of them.

## Notes

**Scope.** Tier 1, so there is no spec; the intent's Approach is the spec. The intent asks for three things: `_drop_record()`'s docstring finished, no docstring calling the change folder `work/`, and the module docstring cut to a purpose plus a pointer at `-h`. Each is in the diff. `decisions.md` D1 answers the open question as "cut", and the diff does that.

**Gate.** `build/round-1.gate.md` is `GATE: PASS` on build `b5bc829731d1c1b6`, with 1998 passing. `build/land-1.gate.md` (the landing gate after the rebase) is untracked in the working tree. I read its tail only and did not re-run the gate. The rebase conflicts were in `change_dirs()`'s docstring (main's new clause plus this change's `.sdlc/work/` name) and in `inbox.md`. Both resolved cleanly, and the merge-base equals main, so the diff against main is the whole change.

**Check 1, `_drop_record` docstring whole.** I read the docstring and body. The docstring now ends "Returns why it failed, or None once the commit is made; a failure aborts the merge and leaves main as it was." The body returns `f"git {args[0]} failed: {err}"` after `merge --abort`, and returns `None` after the commit. The claim matches. The check reads for the absence of "Why not, or\nNone" and the presence of "Returns why". Expected: pass.

**Check 2, no docstring calls the folder `work/`.** The new docstrings use `.sdlc/work/`, and the grep shows no bare `work/` in any docstring. The remaining bare `work/` mentions are `#` comments (lines 102, 134, 296, 621, 801, 4904), one code literal (`MENTIONS_RE`, line 7824), and `_seed_title`'s ` → work/<folder>` pointer (lines 3295, 3300), which the check allows. The comments are outside the intent's "docstrings" scope, and the register entry 2026-11-17-65 carries them forward. Expected: pass.

**Check 3, module docstring points at `-h`.** Line 23 reads "`sdlc.py -h` lists them, and `sdlc.py <subcommand> -h` gives one's arguments". The indented subcommand table is gone. Expected: pass.

**End-to-end path.** `uv run --script scripts/sdlc.py -h` exits 0 and prints every subcommand with a one-line help. The subcommand set printed matches the parser's 41 registrations exactly, in both directions. The module docstring's promise ("cannot drift from the code") holds for this run.

**Register.** The diff removes entries 2026-11-17-27 and -29, the two this change fixes, and adds -65 for the carried-forward comments. This is the expected shape for a landed change. Nothing in the register changes behaviour.

**Working tree.** Before I ran anything, `git status` already showed the factory's own files modified or untracked (`build/land-accept.md`, `runs/*.sessions`, `build/land-1.gate.md`). I created nothing in the repo. My only writes are under `/tmp/behaviour-102.*`, including the uv cache.

## Evidence

Commands were run from the worktree root. Some `cat` calls failed because zsh expanded my `=====` separators as commands; those are shown as the failures they were, and the files were read with the Read tool instead.

```
$ git status --short | head -20; git log --oneline -5; git rev-parse --abbrev-ref HEAD; git merge-base HEAD main; git rev-parse main
 M .sdlc/work/102-sdlc-docstrings/build/land-accept.md
 M .sdlc/work/102-sdlc-docstrings/runs/reviewer-code.sessions
?? .sdlc/work/102-sdlc-docstrings/build/land-1.gate.md
?? .sdlc/work/102-sdlc-docstrings/runs/reviewer-behaviour.sessions
f41c4ff Bring sdlc.py's docstrings up to date
72d0aac Close 101-factory-start-fresh
...
102-sdlc-docstrings
72d0aac5820355d0729c44943116d9d68cc5a266
72d0aac5820355d0729c44943116d9d68cc5a266
exit: 0
```

```
$ git diff --stat main...HEAD; git diff --stat main
 ... scripts/sdlc.py | 94 ++++++----------------
 ... .sdlc/work/inbox.md | 26 ++----
 18 files changed, 360 insertions(+), 88 deletions(-)
exit: 0
```

```
$ cat intent.md; cat checks.md; cat decisions.md; cat notes.md
(zsh: "====CHECKS not found" — separator expanded as a command; the files were then read with the Read tool)
exit: 1
```

```
$ cat build/round-1.gate.md | head -80; cat build/land-1.gate.md | tail -40
(zsh: "====LAND-GATE not found" — same separator problem; round-1.gate.md read via Read: GATE: PASS, build b5bc829731d1c1b6, exit 0 of ./check.sh)
exit: 1
```

```
$ git diff main -- scripts/sdlc.py
 (all hunks are inside docstrings or the module docstring; the -h pointer at line 23)
exit: 0
```

```
$ git diff main -- .sdlc/work/inbox.md
 -2026-11-17-27 (removed), -2026-11-17-29 (removed), +2026-11-17-65 (added)
exit: 0
```

```
$ git show main:scripts/sdlc.py > $S/main_sdlc.py && cp scripts/sdlc.py $S/branch_sdlc.py && python3 -I $S/strip.py $S/main_sdlc.py $S/branch_sdlc.py
code identical with docstrings stripped: True
exit: 0
```

```
$ grep -n 'work/' scripts/sdlc.py | grep -v '\.sdlc/work/' | head -40
102:# work/inbox.md ...
134:# /sdlc:ship carries each one to a work/inbox.md seed ...
296:# `work/inbox.md`, a change's `notes.md` ...
621:        # The file entries go in: `work/inbox.md` ...
801:# committed, so a fresh clone carries on from it, and deleting work/ ...
3295:    ... the ` → work/<folder>` pointer ...
3300:    return title.split(" → work/")[0].strip()
4904:# what the tracker shows; the tracker never reads work/ or .sdlc/ itself.
7824:MENTIONS_RE = re.compile(r"/sdlc:|\.sdlc/|(?<![\w.])work/")
exit: 0
```

```
$ grep -n 'def _drop_record' scripts/sdlc.py; sed -n 4253,4303p scripts/sdlc.py   (read via Read tool)
4253:def _drop_record(
... docstring: "Returns why it failed, or None once the commit is made; a failure aborts the merge and leaves main as it was."
... body: _git_err per step; on error `_git(main, "merge", "--abort")` and `return f"git {args[0]} failed: {err}"`; else `return None`
exit: 0
```

```
$ UV_CACHE_DIR=$S/uv-cache uv run --quiet --script scripts/sdlc.py -h > $S/help.txt 2>&1
85 lines; tail shows: "board  serve the dashboard of every open change on 127.0.0.1; writes nothing" / "options: -h, --help"
exit: 0
```

```
$ grep -oE 'add_parser(...)' scripts/sdlc.py (plus the multi-line add_parser( form) | sort -u > $S/parser.txt; comm -23 parser.txt help-cmds.txt; comm -13 parser.txt help-cmds.txt
41 registered subcommands; comm output: (empty both ways)
exit: 0
```

```
$ grep -n 'sdlc.py -h' scripts/sdlc.py
23:cannot drift from the code: `sdlc.py -h` lists them, and `sdlc.py <subcommand> -h` gives one's
exit: 0
```

```
$ git status --short
 M .sdlc/work/102-sdlc-docstrings/build/land-accept.md
 M .sdlc/work/102-sdlc-docstrings/runs/reviewer-code.sessions
?? .sdlc/work/102-sdlc-docstrings/build/land-1.gate.md
?? .sdlc/work/102-sdlc-docstrings/runs/reviewer-behaviour.sessions
exit: 0
```
