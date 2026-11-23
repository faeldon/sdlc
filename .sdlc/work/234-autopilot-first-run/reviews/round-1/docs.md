VERDICT: PASS

No doc this diff touches says anything false. The diff is `.sdlc/factory.toml` alone: `gate_jobs` goes from 2 to 1 and an `[autopilot]` section with `enabled = true` is added.

- `docs/REFERENCE.md:818-819` says `gate_jobs` is "1 by default". That is still true, and the repo setting now matches it.
- `docs/REFERENCE.md:1635`, `AGENTS.md:283` and `AGENTS.md:315` describe `[autopilot]` and `gate_jobs` as base-branch settings that the factory reads. The diff changes none of that.
- None of the docs I read names this repo's own `gate_jobs` or autopilot values, so nothing there needs to follow the change.

## Notes
- Done well: the header comment in `factory.toml` says why each setting is as it is and that both are for M25's run. That is the right place for the reason, so the docs don't need to carry it.
- Docs read: `AGENTS.md`, `README.md`, `docs/CONTRIBUTING.md` and `docs/REFERENCE.md`. I read the first three only by grepping for `gate_jobs` and `factory.toml`; `README.md` and `CONTRIBUTING.md` had no matches. I also read the change's `intent.md` and the diff. I ran no commands that write, and did not run the gate.
- Unsure: the comment in `factory.toml` points to "M24's 2026-11-22-38". I did not check that this seed exists. Reading `.sdlc/work/inbox.md` would settle it.
