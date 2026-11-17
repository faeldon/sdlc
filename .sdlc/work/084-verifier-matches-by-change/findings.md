# Findings

> What `/sdlc:ship`'s review found, one `## ` section a finding, written after every review and
> committed with the change. A rerun keeps each id, marks one the diff no longer shows `fixed`,
> and never raises again one answered `wrong`, `intentional` or `minor`. `sdlc.py` reads each
> heading and its `Evidence:`, `Class:`, `Disposition:`, `Reason:` and `Fix:` lines, and `By:
> fresh` on a finding the fresh-context reviewer raised, counts them into the `Sdlc-Findings`
> trailer, words ship's question from the ones proposed `fix`, and `ship` refuses while one is
> still `open` or `fix`. On a diff that touches a sensitive path, this note also says `Fresh
> review: ran`, or `Fresh review: skipped, <why>`.

## F1. [important] [correctness] The builder reworks from the verifier's paraphrase, not the reviewer's change

The rework prompt only names `verified.md` and says "Address every KEPT line", and `verifier.md`
now tells the verifier to say each change "in your own words, short". So a kept change reaches the
builder as the verifier's summary, losing what the reviewer actually asked for (078's change was
two sentences with a fallback instruction), although `read_verified()` already resolves each KEPT
answer to the reviewer's text.

Evidence: plugins/factory/scripts/factory.py:1545 (the rework prompt), plugins/factory/agents/verifier.md:44, plugins/factory/agents/builder.md:110
Class: a format change whose downstream reader was left reading the raw file; the board and `measure` read only roles and counts, so the builder is the one reader hit
Disposition: fixed
Fix: the rework prompt lists each kept change of the round as resolved, `- <role>: <the reviewer's text>`, after "Address every KEPT line", saying those are the changes in the reviewers' words; a test in `tests/test_factory.py` that a KEPT answer by id puts the reviewer's text, not the verifier's words, in the rework prompt.

## F2. [nit] [cost] verifier.md's edited paragraphs are wrapped unevenly

"each numbered / with its role (`- C1: code: …`), and from the / factory's script" breaks mid-line,
and the new closing paragraph runs past 100 characters, unlike the rest of the agent file.

Evidence: plugins/factory/agents/verifier.md:17-19, plugins/factory/agents/verifier.md:51-52
Class: hand-wrapped prose left unrewrapped after an insertion
Disposition: fixed
Fix: rewrap both paragraphs to the file's 100-character width, same words.
