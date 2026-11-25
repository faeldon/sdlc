VERDICT: PASS

The docs still tell the truth after this diff.

- **`from_host`:** REFERENCE.md:576–577 says an issue that *opens with* `<!-- sdlc:host-bug:` is flagged `from_host`. The code change to `startswith` now matches that wording.
- **`preflight --preview`:** The new refusal when it is given `--context`, `--nits`, `--bugs`, `--closing` or `--split` isn't documented in REFERENCE.md:888. The sentence there still holds, and the refusal is a behaviour error message. Under the bar for a `[context]` CHANGE, it needs no doc line.
- **Autopilot goal quoting:** The `SKILL.md` text was updated inside the diff itself. No other doc describes how `--goal` is quoted.
- **Other code changes:** `closing.py` now catches `(OSError, ValueError)` and `retro.py` skips excluded host paths. Neither contradicts a doc I read, and each docstring was updated in the diff.
- **Stale lines:** none.

## Notes
- NIT: plugins/factory/skills/autopilot/SKILL.md:99: the new quoting sentence runs past the wrapped width and breaks the file's line wrapping {docs S low}
- Done well: the changed behaviours updated their own docstrings and the `SKILL.md` instructions in the same diff. No duplicate prose went into the context docs.
- Read: AGENTS.md, the REFERENCE.md sections on `from_host` and `preflight`, the full diff of the non-test files, and the first part of `intent.md`. I did not read README.md or CONTRIBUTING.md in full. I only grepped them (and AGENTS.md and REFERENCE.md) for `--preview`, `from_host` and `UPSTREAM_MARKER`. Nothing in them touched this diff. I also grepped `plugins/factory/README.md` for goal quoting and found no match. I did not read the test diffs.
