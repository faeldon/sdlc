VERDICT: PASS

The diff matches the intent: `.github/workflows/check.yml` gets a top-level `permissions: contents: read` block, after `on:` and before `jobs:`. No job sets its own `permissions`, so none widens it.

- **Correctness:** The Linux and Windows jobs only check out, install, lint and test. None pushes, uploads, comments or writes a cache through the repo token, so neither loses a permission it uses. That answers the intent's open question.
- **Contract:** `.github/workflows/` is `[review] sensitive`. The change narrows access and loosens nothing.
- **Context:** No context doc mentions the workflow's permissions, so none is now false.
- **Gate:** `build/round-1.gate.md` records `GATE: PASS`. I did not run the gate or any test.
- **Acceptance check:** I traced the `checks.md` shell block by hand against the file and it should exit 0. I did not run it. It would fail if the block were removed, widened, or declared a second time.

## Notes
- NIT: .github/workflows/check.yml:14: the comment's claim that setup-uv's cache uses the runner's own cache token is an unverified claim about a third-party action. The rest of the comment is checkable from the file. {docs S low}
- Done well: one file, a precise comment that says why the block is enough, and a `checks.md` check that guards against the block being widened or duplicated.
- Ran: read-only `git diff` and `git status`, plus a read of the gate record. No tests run.
