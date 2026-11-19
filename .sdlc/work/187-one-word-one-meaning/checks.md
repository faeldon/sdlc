# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The two test nits are gone

R21 and R22 remove a change citation from a docstring and two comments; only putting them back
could fail this.

```sh
! grep -q '179 R1' tests/test_metrics.py && ! grep -q '# 183' tests/test_skills.py
```

## The arbiter's agent and prompts sit under its name

R12 moves three files with `git mv`; only moving them back could fail this.

```sh
test -f plugins/factory/agents/arbiter.md && test -f plugins/factory/prompts/arbitrate.md && test -f plugins/factory/prompts/land-arbitrate.md && ! test -e plugins/factory/agents/verifier.md && ! test -e plugins/factory/prompts/verify.md && ! test -e plugins/factory/prompts/land-verify.md
```

## The release says what a host must change

R23: the change ships as `minor`, and REFERENCE.md's *After an update* names the removed command,
its replacement for CI and the dropped `[models] verifier`; only deleting the note could fail this.

```sh
grep -q '^impact: minor$' .sdlc/work/187-one-word-one-meaning/intent.md && grep -q 'sdlc.py check` is now `sdlc.py vet`' docs/REFERENCE.md && grep -q 'sdlc.py vet --strict` instead' docs/REFERENCE.md && grep -q '`\[models\] verifier` is now `\[models\] arbiter`' docs/REFERENCE.md && grep -q 'setup proposes it on its next run' docs/REFERENCE.md
```
