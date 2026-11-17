DECISION: ESCALATE

**Why:** All 14 requirements are built and tested by the builder's account. The only reviewer, `code`, passed round 1 with nothing Critical or Required, and the gate is green (2006 tests). But all three decisions in `decisions.md` are still unticked defaults, and D1 goes against the spec as written: R2 said `test_a_diff_touching_no_sensitive_path_runs_light` would "stay green unchanged", and it was changed. The change also alters a published interface: there is a new `[ui] fixture` key, and every host's Tier 2 light rounds now cost one more reviewer by default. And it ran at the light depth with `code` alone, which is the blind spot it fixes. No test reviewer checked its own tests requirement by requirement, and nobody looked at the board fixture in a browser except the builder.

**Open items**
- No CHANGE is open. The code reviewer's Optional items: the `light` line in `cmd_start` now sits under the "Each role's model…" comment, which belongs to the next statement (code). `_fixture_copy` replaces the copy while a server left over from an earlier crashed shot could still be writing to it; the reviewer judged that acceptable (code).
- From `notes.md`: the build skill's summary of `start`'s `ui` doesn't name `fixture`, though the README does (builder).
- From `notes.md`: `test_the_board_fixture_shows_every_card_state` takes about 30s on a cold `uv` cache (builder).

**Decisions to confirm**
- D1: the default moved `test_a_diff_touching_no_sensitive_path_runs_light` and `test_the_ui_reviewers_join_on_a_ui_path_at_either_depth` to Tier 1, instead of keeping them at Tier 2 and expecting `["code", "test"]`. Spec R2 said the first would stay unchanged.
- D2: the default treats a `[light] reviewers` that names no known reviewer as unset (`chosen: false`), so a Tier 2 still gets `test`.
- D3: the default copies a single-file fixture into `fixture/` under its own name, and `{fixture}` names that file.

**For the person at ship**
- Start with `factory.py`: `light_reviewers()`, `depth()`'s "beyond" test (R6, so a Tier 2's own `test.md` never makes a run full), and `_rounds_at_depth()` reading the tier from `intent.md`.
- In `tests/test_factory.py`, check that the two moved tests still pin today's light run (D1), and read the new R1–R8 tests yourself, since no test reviewer did.
- Then `shots()` and `_fixture_copy()`: the copy and removal under `.sdlc/reports/shots/`, the `rmtree` that handles read-only git objects, and that the committed fixture is never written.
- Then `tests/fixtures/board/build.sh` and `serve.sh`. `serve.sh` builds into `<fixture>/drafts`, not `<dir>` as the spec said; `plan.md`'s "As built" section explains this.
- Run `sh tests/fixtures/board/serve.sh "$(mktemp -d)/fixture" 5199` once and look at the page. The code reviewer didn't check the rendered cards.

- IMPACT: minor — hosts gain a new `[ui] fixture` key and `{fixture}` placeholder, and a Tier 2 light run now includes the test reviewer by default. A host that doesn't want the extra cost sets `[light] reviewers = ["code"]`.
