---
id: 123
slug: evidence-reads
kind: spec
created: 2026-11-17
updated: 2026-11-17
---

# 123 — A passing check isn't stopped for a read without its exit · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

Assumptions, each checked in the code:

- **One parser covers both roles.** `read_evidence()` (`plugins/factory/scripts/factory.py`) is the only parser of `## Evidence`. `loop_state()` calls it on the newest builder report and on each round's `RUNS_THE_CHANGE` reply. `land_verdict()` calls it on `reviews/land-<n>/behaviour.md`.
- **No copies exist.** Neither `scripts/board.py` nor `scripts/sdlc.py` holds a copy of the evidence parsing: a grep for `Evidence`, `exit:` and `EXIT_RE` finds none. The intent's constraint ("the board's and `status`'s copies stay pinned") holds as long as no copy is added.
- **The prompt route was already tried.** The behaviour prompt already says "a read included (`head`, `cat`, `ls`): every `$` line gets its `exit:`" (`agents/reviewer-behaviour.md:68`), and the reviewer still leaves it off. Tightening the prompt is the approach that failed.

1. **R1. A read is decided by the script, never by an agent.** A new `is_read(command)` in `factory.py` returns true only for a command the script can tell changes nothing (the rule is in Design). Anything it doesn't recognise is not a read. `test_a_read_is_only_what_the_script_can_tell_changes_nothing` (`tests/test_factory.py`) checks a table of reads and non-reads, and fails if any row is judged the other way.
   - **Reads in the table:** `cat plan.md`, `grep -n x a ; grep -n x b ; cmp a b`, `git -C . show HEAD:a`, `sed -n '1,5p' f`, `jq '.a | .b' f.json`, `awk '$2 > 0 {print $1}' f` and `awk -F, -v n=2 '{print $n}' f`.
   - **Non-reads in the table:** `./check.sh`, `uv run pytest -q | grep passed`, `sed -i s/a/b/ f`, `cat a > b`, `cat $(x)`, `find . -delete`, `git diff --output=f`, `tee f`, `xargs rm`, `X=1 cat f`, `jq . f > g`, `awk '{print > "out"}' f`, `awk '{print | "sh"}' f`, `awk 'BEGIN{system("rm f")}'`, `awk -i inplace '{print}' f` and `awk -f prog.awk f`.
2. **R2. A read that shows its output needs no `exit:`.** `read_evidence()` reports no problem for a `$` command that passes `is_read()` and has at least one non-blank output line before the next `$` line or the section's end. Fence lines don't count as output. `test_a_read_showing_its_output_needs_no_exit` fails if such a reply yields any problem.
3. **R3. A silent read still needs its exit.** If a read prints nothing (a `grep -q`, or a `cmp` of identical files), its exit is its only result. With no `exit:` it is still reported with today's message, ``has no `exit:` line``. `test_a_silent_read_still_needs_its_exit` fails if `$ cmp a b` followed directly by the next `$` line or the section's end passes.
4. **R4. Anything else without its exit still stops or mends, as today.** A test run, a gate, a script, a pipeline with any non-read stage, or a command that writes or redirects to a file, still produces ``has no `exit:` line`` when it has no `exit:`. In the build loop that is still a `mend` once a round and then a stop. The existing parametrized `test_a_builder_report_without_its_evidence_stops_the_run` keeps passing unchanged. A new case, `$ uv run pytest -q | grep passed` with output and no exit (108's round-1 shape), fails the test if it passes.
5. **R5. 119's two landing replies pass.** `test_119s_landing_replies_pass` (`tests/test_land.py`) writes each reply as `reviews/land-1/behaviour.md` of a landing. The first reply is the `grep … ; grep … ; cmp …` chain over `build/round-1.gate.md` and `build/land-1.gate.md`; the second is the mended reply with `cat .sdlc/work/119-ui-review-folders/plan.md`. Each opens `VERDICT: PASS` and gives every command output and no `exit:`. For each, `land-verdicts` must give `next` other than `mend` and `stop`, and its `problems` must not name `exit:`. The test fails if either reply is still a mend or a stop. The fixtures are rebuilt from the commands bug 2026-11-17-90 quotes, with the elided arguments filled in with plausible ones, and the test's docstring says so.
6. **R6. The builder's report follows the same rule.** In `test_a_builders_read_needs_no_exit` (`tests/test_factory.py`), the builder report holds `$ ./check.sh` with its `exit: 0`, then `$ cat plan.md` with output and no exit. `verdicts` must give `review`. The test fails if it stops or mends.
7. **R7. 109's tests keep their meaning.** In `tests/test_land.py`, `NO_EXIT` uses a command that is not a read (`$ uv run pytest -q` with output, no exit). That keeps `test_a_landing_review_missing_an_exit_is_mended_not_stopped`, `test_a_landing_stops_for_cause_even_beside_a_mendable_problem` and `test_a_landing_mend_writes_into_its_landing_round` testing a real missing exit, where today's `head -5 intent.md` would become a pass. `test_a_build_mend_is_refused_when_verdicts_names_none` (`tests/test_factory.py:1889`) gets the same change. A test fails if `NO_EXIT` passes `read_evidence()`, so the fixture can't silently become a read again.
8. **R8. The prompts and docs say the rule.** `agents/reviewer-behaviour.md` and `agents/builder.md` still ask for `exit: <n>` on every command. Their sentence about what the script refuses now reads: a command missing its `exit:` stops the run unless it is a read that shows its output. The behaviour prompt drops "every `$` line gets its `exit:`" as a stated stop. `plugins/factory/README.md`'s *Shown, not said* and `AGENTS.md`'s factory paragraph name `is_read()` beside `read_evidence()`. `test_what_runs_the_change_shows_its_evidence_and_never_runs_checks` (`tests/test_skills.py`) keeps its current asserts. It adds one assert that both prompts carry the phrase "a read that shows its output", and fails if either drops it.

## Design

**`is_read(command: str) -> bool`** sits beside `EVIDENCE` and `EXIT_RE` in `factory.py`, with a comment saying it is the one judge of a read. It is pure: no subprocess and no filesystem access. It errs strict. A command it misjudges as a non-read costs one mend, which is the behaviour today. A command it misjudges as a read would let a claim go unrecorded, so the allowlist is closed and short.

1. **Refuse what can't be seen into.** Outside single-quoted text, a command containing a backtick, `$(`, `<(` or `>(` is not a read. The shell substitutes nothing inside single quotes, so a quoted awk `$(NF-1)` or jq `$x` is fine.
2. **Tokenise** with `shlex.shlex(command, posix=True, punctuation_chars=True)` and `whitespace_split = True`. A quoted program (jq's filter, awk's program) stays one token, its `|` and `>` included. A `ValueError` (unbalanced quotes) means not a read.
3. **Split into simple commands** at the tokens `|`, `||`, `&&` and `;`. Any other token made only of punctuation that isn't a redirection (`&`, `;;`, `|&`, `(`, `)`) means not a read.
4. **Redirections.** `<` is allowed. An output redirection (`>`, `>>`, `>&`, `&>`, with or without a leading descriptor digit) is allowed only to `/dev/null` or to a descriptor (`2>&1`). Anything else means not a read.
5. **Each simple command must be a read.** A leading `NAME=value` assignment means not a read. The first word, bare with no path, must be in `READS`, under that program's own condition:
   - **Plain reads:** `cat`, `head`, `tail`, `grep`, `egrep`, `fgrep`, `rg`, `ls`, `wc`, `cmp`, `diff`, `nl`, `cut`, `tr`, `stat`, `file`, `pwd`, `cd`, `echo`, `true`, `test` and `[`.
   - **`jq`:** always a read under steps 1–4. jq has no builtin that writes a file or runs a command, so the shell's redirections are its only way to write.
   - **`awk`:** a read only when all of these hold:
     - none of the options `-f`, `--file`, `-i`, `--include`, `-l`, `--load`, `-E` or `--exec` is present. These read the program from a file the script can't see, or load an extension such as gawk's `inplace`. `-F` and `-v` are allowed.
     - the program (the first argument that isn't an option) contains no `|`, no `system(`, no `@load` and no `@include`.
     - no `print` or `printf` statement in it holds a `>` before the statement ends at `;`, `}` or a newline.

     A `>` in a pattern or condition (`$2 > 0 {print $1}`) stays a read. A comparison inside a print (`print ($1 > 2)`) is refused, which errs strict and costs at most a mend.
   - **`sort`:** only without `-o` or `--output`.
   - **`sed`:** only without `-i` or `--in-place`, and only when every script argument is an address (digits, `,`, `$`, or `/regex/`) followed by `p`. Any `w`, `W` or `e` command therefore never passes.
   - **`find`:** only without `-exec`, `-execdir`, `-ok`, `-okdir`, `-delete` or any `-fprint`/`-fls` predicate.
   - **`git`:** after optional `-C <path>` and `--no-pager`, the subcommand must be one of `show`, `diff`, `log`, `status`, `rev-parse`, `ls-files`, `ls-tree`, `cat-file`, `grep`, `blame`, `merge-base`, `shortlog` or `describe`, with no `--output`, `-O` or `--open-files-in-pager` option.

   Everything else is not a read: `gawk`, `mawk`, `uniq` (which writes its second operand), `python`, `uv`, `pytest`, `sh`, `bash`, `env`, `xargs`, `tee`, `make`, any `./script`.

**`read_evidence()`** changes in one place. Today a command left open at the next `$` line or the section's end is reported. Now the function also tracks whether the open command printed a non-blank, non-fence line. When it closes a command with no `exit:`, it reports only if `not (is_read(cmd) and printed)`. The problem text stays the same, so these readers are untouched: the `mend` routing in `loop_state()` and `land_verdict()` (`set(problems) <= every`), the build and land skills' wording, and the board's fixture `006-draft-purge/runs/stopped.md`. The "no section" and "no command run" checks don't change: a reply of nothing but reads still has commands, and still has its section.

**Callers don't change.** `loop_state()`, `land_verdict()` and the `MEND` and `land-mend` prompts all go through `read_evidence()`. The change stays inside `read_evidence()` and one new function near the constants at the top. That keeps it out of the regions that 121 (landing-review-base) and 112 edit in `factory.py`, so rebases stay small.

**The builder gets the same rule.** The code answers this: one parser serves both roles, and a split would need a role argument and a second rule to keep in step. The builder's prompt asks only for the commands its claims rest on. Its gate and test runs are never reads, so they still owe their exit. That was 108's case (`pytest … | grep`), which R4 pins.

## Contracts touched

- **"A builder report and a behaviour check end with `## Evidence` (`read_evidence()`); a reply missing it … is the one stop a run mends"** (AGENTS.md, the factory). The section is still required, a `$` command is still required, and a missing exit on anything but a read that shows its output is still a mendable stop, once a round, a landing round counting as its own. The contract narrows by one named exception, decided by the script, never by the agent. The factory paragraph is edited to name `is_read()` (R8). This is a policy-doc edit the intent asks for, not a side effect.
- **"No claim may rest on a command whose result nobody recorded"** (the intent's constraint). A read is excused only when its printed output, which is its result, is in the reply. A read whose only result is its exit (R3) is not excused.
- **"A reply is never patched by the supervisor"** (the intent's contracts). The script only reads the reply. No agent's text is edited or filled in.
- **Copies of parsing are pinned by tests** (AGENTS.md, the board and `factory.py`). No copy of `read_evidence()` exists in `sdlc.py` or `board.py` (checked), so nothing new needs pinning. The problem strings the board's fixtures hold are unchanged.
- **The scripts run on Windows** (`tests/test_windows.py`). `shlex` is stdlib, nothing is imported per platform, and nothing is run or written.
- **No agent but the builder runs `checks.md`.** Untouched. The behaviour prompt's *checks.md: read, never run* section stays word for word.
- **Nothing public names the agent; nothing local.** R5's rebuilt fixtures use only paths inside a change folder (`.sdlc/work/119-ui-review-folders/…`), the plugin's own history, as other tests already cite 109 and 103. No home path appears.

## Alternatives rejected

- **Tighten the reviewer's prompt and keep the rule.** 109 chose this, and the prompt already names `head`, `cat` and `ls` and says every `$` line gets its exit. 119's reply and its one mend both left the exit off a read. A rule the agent keeps missing, on a command that can't change the outcome, stops passing changes (O3, O6).
- **Drop the `exit:` requirement altogether.** This breaks the intent's second outcome: a test run or gate claimed without its exit would pass.
- **Let the agent mark its own reads** (say, an `exit: n/a` or `# read` tag). This puts the judgement back on the agent the rule exists to check, and a mislabelled test run would pass.
- **Exempt a read by its first word alone.** `cat a > b`, `sed -i`, `find -delete`, `awk '{print > "f"}'` and `pytest | grep` would each pass. The pipeline, redirection and per-program rules above exist for exactly these.
- **Parse awk programs fully** to tell a comparison from a redirection in every position. It's a grammar for one program's edge cases. The statement-level check refuses only prints holding a `>`, which costs at most one mend.
- **Infer the exit from the output** (for example "no error printed"). A silent `cmp` or `grep -q` can't be told apart from a failure, and the script would be guessing a result.
- **A mend that patches in `exit: 0` for reads.** The supervisor never writes into an agent's reply.
- **A second mend for evidence.** It costs another paid call per round, and 119 shows a second ask gets the same reply.

## Verification

- `uv run --group dev pytest -q tests/test_factory.py tests/test_land.py tests/test_skills.py -k "evidence or read or exit or 119 or landing or mend"`: every case passes, including the new R1–R8 tests and 109's tests with the new `NO_EXIT`.
- `uv run --group dev pytest -q -m portable`: passes. `is_read()` is pure, so its table test is marked `portable`.
- `./check.sh`: ruff and the format check are clean, all of pytest passes, and `claude plugin validate --strict` passes.
- **By hand, before ship:** feed `read_evidence()` R5's two fixtures, then the same fixtures with `$ uv run pytest -q` swapped in. Healthy is `[]` for the first and one ``has no `exit:` line`` problem for the second.

