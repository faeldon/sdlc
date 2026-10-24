---
id: 003
slug: test-lifetimes
kind: spec
created: 2026-10-24
updated: 2026-10-24
---

# 003 — Enforce shim deadlines, and sweep acceptance-only tests · spec

> Tier 2 only. Reads from intent.md; read by plan.md. If you can't write a testable requirement
> list, the intent isn't understood yet — go back to Stage 1 rather than designing around the fog.

## Requirements

1. **R1. The key.** `release.deprecations` (default `.sdlc/deprecations.toml`) names the registry.
   It is resolved once in `load_config()` and printed by `config`. While the file is absent the
   feature is off: no output changes, and nothing refuses. A test covers a bare repo with no file.
2. **R2. The format.** Each shim is one `[[shim]]` table:
   - **Required:** `name` (unique), `remove_in` (a quoted `X.Y.Z` string) and `where` (text,
     usually a path).
   - **Optional:** `test` (the compatibility test that covers it).
   - **No other key** is allowed.

   One function, `deprecations(home, cfg) -> {"shims", "problems"}`, reads it. It never raises:
   each of these is a problem naming the entry:
   - TOML that won't parse;
   - a top level other than `shim = [...]`;
   - a missing, unknown or non-string key;
   - a duplicate `name`;
   - a `remove_in` that isn't `X.Y.Z` (so `remove_in = 1.10` is refused rather than read as
     `1.1`).

   An entry with a problem is left out of `shims`. One test per problem.
3. **R3. Due and overdue.** `unreleased()` gains `deprecations: {"overdue", "due", "unversioned"}`,
   compared with 002's `_older()` and `_semver()`:
   - **Overdue:** `remove_in` ≤ the current version (`release.version_files`).
   - **Due:** not overdue, and `remove_in` ≤ `next`, the version the next release would cut.
   - **Unversioned:** with no `version_files`, or no readable version, every shim is listed here
     and nothing is compared.

   Registry problems join `unreleased()`'s `problems` before the bump is computed, so they block a
   release the way a bad intent does. Tests cover each case, including `1.10.0` > `1.9.0`.
4. **R4. Release refuses.** `cmd_release`, `--check` included, refuses while any shim's
   `remove_in` ≤ the version it would cut, whether that's `next` or `--version`. Each refusal names
   the shim, its `where` and its `test`. Nothing is written first. A test proves the refusal;
   another proves a shim due later doesn't refuse.
5. **R5. Status warns, never gates.** In the Unreleased block:
   - `⚠  shim <name> is overdue: remove in <v> (<where>)` for each overdue shim;
   - `⚠  shim <name>: remove in <v> (<where>)` for each due one.

   Neither joins `analyze()`'s problems, so `check --strict` exits 0 with an overdue shim (a test).
   With the feature off, `status` output is byte-for-byte unchanged (a test).
6. **R6. This repo dogfoods it.** `.sdlc/deprecations.toml` holds a header comment and no entries:
   this repo has no shim today. A gate test reads it through `deprecations()` and fails on:
   - any problem;
   - any shim with `remove_in` ≤ `plugin_version()`;
   - any `test` that doesn't name an existing `tests/<file>::<function>`.

   A fixture proves it fails on an overdue shim and on a missing test.
7. **R7. Docs.**
   - **`docs/REFERENCE.md`:** the key in the config sample, and a paragraph in `## Releases`
     covering the format, due versus overdue, the refusal and the status lines.
   - **Stage 4's Compatibility line,** in `defaults/SDLC.md` and `.sdlc/SDLC.md`, identically:
     "…which names the version that removes it, in `release.deprecations` when the repo keeps one,
     else in a comment; the test goes with the shim."
   - **`AGENTS.md` Releasing:** "A shim in `sdlc.py` gets an entry in `.sdlc/deprecations.toml`,
     and `cmd_release` refuses a version that would still carry it. A path kept for good (the
     no-manifest drift, `RETIRED_KEYS`) is not a shim and has none."
8. **R8. The sweep.** Each site is found by its content, and each outcome gets one line in
   `notes.md`.
   - **Removed, since only a revert could fail them:**
     - `"tokens" not in out` (`test_retro.py`);
     - `work/.last-id` absent (`test_sdlc.py`);
     - the counter under `<git-dir>/sdlc` absent (`test_sdlc.py`, `test_adoption.py`);
     - `"sdlc.py archive" not in text`, keeping `"rm -"` (`test_skills.py`);
     - `"archive"` in the writer tuple (`test_readiness.py`);
     - the `.sdlc/ids` allowance (`test_archive.py`);
     - `"claude plugin uninstall sdlc@sdlc"` in
       `test_uninstall_plans_before_its_gate_and_removes_after`, keeping its gate-order checks.
   - **Rewritten to the rule they stand for:**
     - `len(_bash_rules(skill)) == 8` in `test_setup_asks_what_kind_of_repo_first` becomes "no
       rule runs `git log` or `gh`";
     - `test_the_shipped_defaults_have_one_block_per_key` asserts its glob found files.
   - **Added:** a regression test for `uninstall` with no manifest, which leaves the ignore line in
     place. It's the one branch of the permanent no-manifest path with no test.
   - **Judged one by one at build,** each removed or kept with its reason: `test_readiness.py`'s
     `"### Stage 4 — Test"`/`"/sdlc:setup"`, `test_skills.py`'s "Since the last retrospective",
     `O1 (Unaided setup)` and the three retro phrases, and `test_playbook.py`'s loop phrases.
   - **Never touched:** a test guarding an `AGENTS.md` invariant. The gate stays green.

## Design

`deprecations()` sits beside `read_versions()` and reads with `tomllib`. It checks types itself, as
`load_config()` does. `shims_due(shims, current, nxt)` returns overdue and due using `_older()`.
`unreleased()` calls both once, so `status`, `unreleased` and `release` share one computation.
`cmd_release` adds a refusal per shim with `remove_in` ≤ `new`, after the `--version` handling.
`print_status` prints from `a["release"]["deprecations"]`, and the Unreleased block's guard also
opens when shims are listed.

The key sits under `[release]` because what it gates is a release, compared against what
`release.version_files` hold. A single path with a string default, it's on only while the file
exists, as `docs.product` is.

No skill changes: `/sdlc:release` already shows `refusals`, and `/sdlc:status` prints what `status`
prints, so no WAIT and no `allowed-tools` move.

Edge cases:
- A `--version` past `remove_in` refuses.
- An empty file has no shims and no problems.
- Disagreeing version files are already a problem and block the comparison.

## Contracts touched

- **Mechanism vs. policy:** the path comes only from `config`. Kept.
- **Read as text, never YAML:** TOML strings, and an unquoted number is refused. Kept.
- **The release boundary:** unchanged; the comparison never reads a tag.
- **What `sdlc.py` reads in a host:** a new key and file (Tier 2). Off while absent, and no other
  output changes. `test_adoption.py` still runs a bare repo end to end.
- **`check --strict` is a gate:** shims never join `analyze()`'s problems, matching 002's drift
  nudge.
- **Release is local:** release gains a refusal and still writes nothing before deciding.
- **The defaults and this repo's copies:** the Stage 4 edit lands in both.
- **002, landed:** `plugin_version()` and `_older()` are reused.
  - **`RETIRED_KEYS`** lists keys the plugin *stopped* reading, so a host hears about them. No old
    code runs, so they aren't shims.
  - **The no-manifest path** (two-way drift, the "no record" nudge, uninstall leaving the ignore
    line) serves any host without a readable record, not only 1.0.0 hosts. It is kept for good,
    and is not registered (decided 2026-10-24).
- **Nothing local:** fixtures use neutral names (`old-flag`).

## Alternatives rejected

- **A `compat` pytest marker:** this repo only, and `test` covers it in any host.
- **A gate test against the current version alone:** it fails only after the release that should
  have removed the shim.
- **A Python constant for the plugin's shims:** a second mechanism. Dogfooding the file tests the
  host path on every gate.
- **A host command (hook):** a second code path, for hosts that have none yet.
- **Overdue shims under Problems:** one overdue shim would fail every unrelated change's
  `check --strict`.
- **Registering the no-manifest path with `remove_in = "1.3.0"`:** a 1.0.0 host's first rerun
  after that would record today's defaults as its base, so every update since 1.0.0 would read as a
  host edit and never be proposed. The path also serves a missing or broken record, so it never
  goes.
- **A `keep` field for permanent paths:** nothing to register, since a permanent path isn't a shim.
- **Removing the medium sweep candidates unexamined:** several pin wording a skill's model follows.

## Verification

```bash
./check.sh                                                # all pass
uv run --group dev pytest tests/test_deprecations.py -q   # R1–R6
uv run --quiet --script scripts/sdlc.py unreleased        # "deprecations": {"overdue": [], "due": [], "unversioned": []}
uv run --quiet --script scripts/sdlc.py status            # unchanged with no shims
```

Acceptance, recorded in `notes.md`: add a scratch shim with `remove_in = "1.0.1"` to a scratch
clone's registry. `release --check` should refuse it by name, `unreleased` should show it in
`due`, and `status` should show its line. Then discard the clone.
