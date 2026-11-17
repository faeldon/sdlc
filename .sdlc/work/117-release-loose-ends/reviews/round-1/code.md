VERDICT: PASS

I found no Critical or Required findings. All twelve requirements have code and a test that would fail without it, and the gate is green.

## Notes

- **R6 test deviates from the spec's wording.** The spec says a hint with neither commit keeps `<the commit that released it>`. That fallback is kept in the code, but no new test pins it. Optional.
- **Unused `adopt` path in the hint.** `later = last and adopt and last != adopt` is a string or `None`, not a bool. It works, but a plain `if last and adopt and last != adopt and ...` would be clearer. Nit.
- **Duplicated `git fetch` environment.** `_fetch_notes` repeats `_push()`'s subprocess setup (`GIT_TERMINAL_PROMPT=0` and closed stdin). That is acceptable, since the spec says the fetch must not go through `_push`.
- **`changelog_section` ordering.** It replaces `{{notes}}` last, so a note that contains `{{version}}` stays as written. This is a good detail.
- **Done well.** The changelog tests cover the no-marker path against today's exact bytes, including CRLF and empty files. The marker test checks that everything above the marker is byte-identical. The second-clone tests use a real counter file outside both clones, so they exercise the actual skip. Docs, the skill, AGENTS.md and the `EXCEPTIONS` entry all moved together.
- **Ran:** `./check.sh`. ruff passed, pytest gave 2209 passed and 9 skipped, and `claude plugin validate --strict` passed. The factory plugin shows an icon warning that the validator says does not change the result.
- **Not run:** I did not run the manual scratch-repo publish check from the spec.
