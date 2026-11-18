# 150 — Plan

> Tier 1, written because the Approach touches more than a couple of files: what changes, in
> what order, which test proves each behaviour, and what a revert wouldn't undo.

## Files to change

- `plugins/factory/scripts/factory.py`
  - -72: `_defused(text, root=None)` reads the main checkout's `.sdlc/terms.local` (`_terms()`,
    found through the existing `_all_checkouts()`, the way `test_nothing_local.main_checkout()`
    finds it) and writes each match as `TERM_MARK` (`<term>`). `_placeholders()` and
    `cmd_defuse()` pass `root`; `forbidden_lines(folder, root=None)` refuses the terms too, so
    `defuse` can rewrite a hand-filed line and the approver's stop names it (by path and line
    only, never the term).
  - -48: a comment on `replies[-1]` in `cmd_agent()`: `_claude()` returns a non-empty list
    whenever it returns no problem.
  - -51: `stop_text`'s `stuck`, `untestable` typed `list[str] | tuple = ()`.
  - -62: `_own_folder()`'s `\*?` made possessive (`\*?+`, Python ≥ 3.11), so the lookahead
    can't pass on a `*` backtracked off.
- `scripts/sdlc.py`
  - -72: `_hand_placeholders()` applies the same terms (`_hand_terms()`, `TERM_MARK`), a copy
    pinned by `tests/test_hand_gate.py`.
  - -52: a comment at `status`'s ready-list `needs_of` call: at `shipped` `needs_of()` reads only
    `problems` and `land_stop`; a field it reads there later is added here.
  - -57: `_passes_report()`: with the factory enabled and no shots, `ui.why` ends with the
    command that takes them, `factory.py shots NNN --round 1 --role ui` (the bare `shots NNN`
    the intent names is refused: both flags are required); ship never runs it.
- `skills/ship/ui.md` (-57, the same pointer), `behaviour.md`, `security.md`, `ui.md` (-58,
  "a factory run, whose own reviewers ran"), `security.md` (-59, "a deep diff").
- `AGENTS.md` (-53, line breaks only), `plugins/factory/agents/reviewer-code.md` and
  `reviewer-ux.md` (-55, wrap the `supersedes` sentence), `plugins/factory/README.md` (-63,
  rewrap the paragraph at the `serve`, `shoot` and `paths` line).
- `tests/test_factory.py` (-54 docstring, -56 assert, -62 and -72 tests), `tests/test_hand_gate.py`
  (-72 pin), `tests/test_preflight.py` (-57).

## Work order

1. -72, factory: test a reply quoting a fixture term is filed as `<term>`, and `defuse` rewrites
   a hand-filed one; then `_terms()`, `_defused(root)`, `forbidden_lines(root)`.
2. -72, sdlc copy: extend `test_the_placeholders_are_the_factorys` with a terms file; then the copy.
3. -62: test `work/NNN*x` keeps its `*`; then the possessive quantifier.
4. -57: test `ui.why` names `factory.py shots NNN` when the factory is enabled; then the code
   and `ui.md`.
5. -56, -54, -48, -51, -52: test assert, docstring, comments, annotation.
6. Docs: -58, -59, -53, -55, -63.

## Tests

- -72: `test_a_reply_quoting_a_local_term_is_filed_as_a_placeholder` (factory), and the extended
  `test_the_placeholders_are_the_factorys` (the copy agrees).
- -62: `test_a_reply_citing_its_own_change_by_number_is_filed_by_its_full_name` gains the
  `work/NNN*x` case.
- -57: `test_preflight_passes_ui` gains the factory-enabled case.
- -56: the "unverified" case asserts `next == "rework"`.
- Docs: `checks.md`'s three acceptance checks (AGENTS.md's line length, the wrapped sentences
  and README paragraph, the pass files' wording); comments and the annotation by the gate.

## Rollback

Nothing outside git: `git revert` undoes all of it.
