DECISION: READY

**Why.** The builder's report and the code reviewer's round-1 pass give every requirement R1–R13 code and a test that fails without it. The script gate passed on its first attempt: `./check.sh` ran 1913 tests, ruff was clean and `validate --strict` passed. `drift` and `check --strict` report nothing. No finding is above Optional, the reviewer and builder never disagreed, the build follows the spec and `plan.md` explains both places where it differs (the fixture is a copy rather than an `extends`, and there's one extra sentence in `AGENTS.md`). Without the factory, every path works as it does today.

**Open items**
- R11 is only partly met (code reviewer, Optional). The spec says both `intent` cases also check R4's wording, but no grader checks the question's endings: the `intent-product` regex stops at `serving`. `tests/test_skills.py` still pins the wording. This gap is not recorded in `notes.md`. Ship should give it a disposition: tighten the regex, or note it as unmet.
- `factory_enabled` uses `named[0] is True` (code reviewer, Optional). When a settings file has two `sdlc-factory@` keys, the first one decides; `any(...)` would be more forgiving.
- Nit (code reviewer): in Step 0 of `skills/intent/SKILL.md`, the factory note and `Note git.base too:` sit on one over-long line.
- R12 was reviewed only by its diff stat (code reviewer). Nobody has read the wording of the README, `docs/REFERENCE.md` or `plugins/factory/README.md`.
- The paid `run-cases --tag intent` (`intent` and `intent-product`) hasn't run. Ship names it.

**Decisions to confirm**
- None. There is no `decisions.md`, and the builder raised no decisions.

**For the person at ship**
- Check `factory_enabled()` and its place in `cmd_config()` in `scripts/sdlc.py` first. This is the core's first read of `~/.claude/settings.json` and of `enabledPlugins`. Confirm it only reads, runs no subprocess, and that a bad file falls back to no factory.
- Next, check Steps 4–6 in `skills/intent/SKILL.md`. The question without the factory should be word for word the old one, and `yes, for the factory` should skip both `EnterWorktree` and `EnterPlanMode`.
- Then read the three docs' wording, which no reviewer has done.
- Watch for the new fixture file `evals/fixtures/product/change/.claude/settings.json`. If `risk_paths()` matches it as a substring of the sensitive pattern `.claude/settings.json`, ship's review becomes deep and a land stops at its gate.

- IMPACT: minor — with the factory enabled, `/sdlc:intent` now offers `yes, for the factory`, which skips plan mode and keeps the session in the main checkout. `config` also gains a `factory` object. Hosts without the factory see no change.
