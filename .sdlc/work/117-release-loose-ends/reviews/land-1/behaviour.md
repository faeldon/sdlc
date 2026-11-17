VERDICT: PASS

The tests the spec names pass, and the diff matches R1–R12 on a read. I didn't run a scratch publish from two clones; `test_a_second_clone_skips_the_upload_another_made` covers that path.

## Notes
- **`checks.md`:** the change has none, so there was nothing to read or run.
- **Gate:** the landing gate record `build/land-1.gate.md` is green (plugin validation passed). I did not rerun it.
- **R1/R2 (changelog):** `with_changelog` takes the first line that strips to the marker and inserts the section after it. Everything above the marker is kept as it was. With no marker it follows today's path.
- **R3/R4 (template):** `changelog_section` fills the template with `str.replace`, and `{{notes}}` is filled last so a placeholder inside a note stays as written. `changelog.md` is in `DOC_TEMPLATES` and `TEMPLATE_READS`.
- **R5 (version line):** the new `VERSION_RE` keeps the key at the start of the line, so `target-version` and `my__version__` are still not version lines.
- **R6 (missing-tag hint):** the hint names the adoption commit only when the last version commit is a strict ancestor of it. Otherwise it names `last or adopt`, then the placeholder.
- **R7–R10 (publish notes):**
  - The fetch is not forced, goes into a mirror ref, and only runs when there is a publish command and the run is not `--check`.
  - The notes push goes through `_push()`, and a refusal sets `notes_push_failed` without failing publish. That gives the exit 0 the spec asks for.
  - A rerun skips the push when the remote already holds the ref.
- **Not run:** `tests/test_release.py` holds the tests for R11 and R12 (REFERENCE.md and the publish skill). I did not read the REFERENCE.md or `skills/publish/SKILL.md` diffs, only that those tests pass.

## Evidence
$ uv run --group dev pytest -q tests/test_release.py tests/test_push.py tests/test_defaults.py tests/test_skills.py -n auto 2>&1 | tail -5
577 passed in 10.98s
exit: 0

$ uv run --quiet --script scripts/sdlc.py drift 2>&1 | tail -5
        ]
      }
    }
  }
exit: 0
(The `exit: 0` above is the `echo` after the pipe, so it reports `tail` and not `drift`. The tail is JSON closing braces and names no drift entries, so I take it as no drift reported, but I did not read the full output.)

$ git diff main...HEAD -- scripts/sdlc.py | head -300
(diff read: `VERSION_RE`, `_adoption_commit`, `unreleased()`, `changelog_section`, `with_changelog`, `_fetch_notes`, `cmd_publish` and `TEMPLATE_READS`)
exit: 0

$ ls .sdlc/work/117-release-loose-ends; cat intent.md checks.md decisions.md; git log --oneline -5; git diff --stat main...HEAD
(`checks.md` and `decisions.md` do not exist; `intent.md` read)
exit: 0

$ sed -n 1,200p spec.md; tail -15 build/land-1.gate.md
(spec read; the landing gate record ends "✔ Validation passed")
exit: 0
