---
id: 012
slug: nits-register
kind: plan
created: 2026-10-25
updated: 2026-10-25
---

# 012 — A ship's unfixed nits are kept, weighed and paid down by theme · plan

## Context

A nit ship approves unfixed lives only in the `Sdlc-Findings` count; nine are open and remembered
only by a seed's prose. The spec (`work/012-nits-register/spec.md`, R1–R13) adds a register,
`work/nits.md`: ship captures and retires entries, intent and spec offer pickup, retro weighs the
debt by theme and age, under a rubric in the process doc. Release and publish stay out. Saved as
`work/012-nits-register/plan.md` once approved. One change, built in the order below; each step
leaves the gate green.

## Entry format (R1, the contract every step reads)

```
## 003-1 [robustness] status crashes on a registry that isn't UTF-8
- **raised:** 2026-10-24 by 003-test-lifetimes (correctness)
- **paths:** scripts/sdlc.py
- **cost:** S  **value:** med

One or two lines: what's wrong and where.
```

Id `<NNN>-<n>`; theme free text in brackets; cost `S|M` (L never lands: it's a seed); value
`med|low`.

## Work order

1. **`scripts/sdlc.py` — reading the register (R2, R3, R11).**
   - `NIT_RE = re.compile(r"^##\s+(\d{3,}-\d+)\s+\[([^\]]+)\]\s+(.+)$")` beside `IDEA_RE` (line 132);
     `NIT_COSTS = ("S", "M")`, `NIT_VALUES = ("med", "low")`.
   - `nit_entries(root) -> tuple[list[dict], list[str]]` beside `idea_entries()` (line 865): reads
     `work_dir(root) / "nits.md"` as text (`errors="replace"` would hide a bad file, so a
     `UnicodeDecodeError` is a problem, not a crash); each heading starts an entry; `- **raised:**`,
     `- **paths:**`, `- **cost:** … **value:** …` bullets parsed with small regexes; prose kept. Problems:
     a heading `NIT_RE` can't read, a missing bullet, a bad date (`date.fromisoformat`), cost/value
     outside the tuples, a duplicate id. Missing file → `([], [])`.
   - `cmd_nits(root, touching, change)`: JSON `{"path", "nits": [... + "age_days"], "problems"}`.
     `--change NNN`: `_one_change()` → its checkout (`path.parent.parent`) → `changed_paths(checkout,
     "main")` (line 4625) gives the paths, both sides of a rename. `--touching p…`: given paths. A nit
     matches when a nit path equals a changed path or is a directory prefix of one (`p == q or
     q.startswith(p.rstrip("/") + "/")`). Exit 1 on problems.
   - `analyze()` (line 884): append `{"dir": "work/nits.md", "kind": "nits", "detail": p}` per
     problem, so `check --strict` fails on a malformed register.
   - `retro()` (line 3637): `"nits": {"open": n, "themes": {theme: {"count", "oldest", "age_days"}}}`
     beside `"ideas"`. Empty register → `{"open": 0, "themes": {}}`.
   - `DOC_TEMPLATES` (line 246) gains `"nits.md"` so `config` names it. Not in `READ_ONLY` (R13).
   - Parser: `p_nits = sub.add_parser("nits", ...)` with `--touching nargs="*"` and `--change`.
2. **`templates/nits.md` (R1).** `# Nits`, a `>` note (what the file is for, that ship writes and
   retires entries and retro counts them), then a `## How an entry reads` section holding the format
   above as a fenced example. `nit_entries()` must skip fenced lines, so the example isn't an entry:
   reuse `FENCE_RE`. Shape rules in `tests/test_defaults.py` pick it up by glob.
3. **Tests — `tests/test_nits.py` (new), loading `sdlc.py` by path like the others.**
   - parse a good register (fields, `age_days` with a fixed `today`); each problem kind;
     missing file → empty, exit 0; the template's own example isn't an entry (R1, R2);
   - `--touching` and `--change` against a scratch repo with a branch (reuse `tests/test_sdlc.py`'s
     repo helpers) (R2);
   - `check --strict` fails on a bad register, passes with none (R3, R11);
   - `retro()["nits"]` counts and oldest per theme, and `{"open": 0, ...}` with none (R7, R11);
   - this repo's own `work/nits.md` parses with nine entries and no problems (R12);
   - R9: `"nits"` appears in neither `skills/release/SKILL.md`, `skills/publish/SKILL.md`, nor the
     source of `cmd_release`/`cmd_publish` (`inspect.getsource`);
   - R10 needs no new test: existing `metrics_summary` and trailer tests stay unedited.
4. **Skills (R4–R7, R13).** Each gains `'Bash(uv run --quiet --script "${CLAUDE_PLUGIN_ROOT}"/scripts/sdlc.py nits *)'`.
   - `skills/ship/SKILL.md`: Step 0 runs `sdlc.py nits --change <NNN>`. Step 3 ranks Nits under the
     process doc's rubric (theme, paths, cost, value; L → seed). Step 4 shows nits to add and nits to
     retire (fixed or moot, with a reason), and a `Retired nits:` paragraph in the message. WAIT gains
     `, with its nits recorded in work/nits.md` when there are any to add or retire. Step 6 appends
     entries (`Write` from `templates["nits.md"]` first if absent; ids `<NNN>-<n>`), deletes retired
     ones, and stages `work/nits.md`. `Write` remains for new files only.
   - `skills/intent/SKILL.md` Step 1 (Tier 1 path) and `skills/spec/SKILL.md` Step 1: run `sdlc.py
     nits`, list open nits whose paths or theme match the change, offer the S-cost ones; taken ones
     named in Approach / Requirements. Nothing listed when none.
   - `skills/retro/SKILL.md`: Step 0's counts include `nits`; the architecture or process pass applies
     the process doc's paydown threshold and may propose one seed per theme. Never edits
     `work/nits.md`.
   - `tests/test_skills.py`: `READS_CONFIG` adds `docs.process` to ship and spec (they apply its
     rubric); a test that ship's WAIT names `work/nits.md`, ship Step 0 runs `nits --change`, intent
     and spec run `nits`, and retro never `Edit`s it.
5. **Process docs (R8).** `defaults/SDLC.md` and `.sdlc/SDLC.md`: a `### Nits` subsection in the
   review/ship part: the rubric (cost S/M/L, value med/low, high isn't a nit, L → seed, S+med
   offered at ship), the default themes, the retro threshold (5 per theme or older than 60 days),
   and that release/publish don't touch it. Same words in both (memory: defaults mirror into
   `.sdlc/`). Then `uv run --quiet --script scripts/sdlc.py record`.
6. **This repo's data (R12).** `work/nits.md` from the template with the nine: 003-1, 003-2
   (raised 2026-10-24, `003-test-lifetimes`), 005-1..3 (2026-10-24, `005-acceptance-checks`), 009-1
   (2026-10-24, `009-drift-message`), 010-1..3 (2026-10-24, `010-release-lock`). Paths, pass and
   detail taken from each change's ship commit message and `notes.md` in history (`git show`), not
   from memory. The seed itself leaves `work/ideas.md` at ship (Step 6, by `idea:`).
7. **Reference.** `docs/REFERENCE.md`: one line for `work/nits.md` and `templates/nits.md` beside
   `ideas.md`. AGENTS.md is the ship context pass's call.
8. **Gate.** `./check.sh`; `git status --short` shows only this change's files (`uv.lock` unchanged).

## Tests (by requirement)

R1 template shape (existing glob) + example-not-an-entry; R2–R3, R7, R11, R12 `tests/test_nits.py`;
R4–R6, R13 `tests/test_skills.py` (rules tests cover every new bash line); R8 `tests/test_defaults.py`
(mirror) + drift gate; R9 `tests/test_nits.py`; R10 existing tests unedited.

## Verification

- `./check.sh` green.
- `uv run --quiet --script scripts/sdlc.py nits` → nine entries, `problems: []`.
- `… nits --change 012` → those whose paths this branch touches.
- `… retro` → `nits.themes` with counts.
- `… drift` → nothing.

## Rollback

`git revert <sha>`. A host that already has `work/nits.md` keeps a file nothing reads; harmless.
