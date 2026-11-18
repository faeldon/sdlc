# Checks

> The change's acceptance checks: each `## ` section is one, which only a deliberate revert could
> fail, so it stays out of the suite. `/sdlc:ship` reruns every one from the checkout root before
> it commits, and a check passes when its one `sh` block exits 0 and leaves the working tree as it
> found it. `sdlc.py` reads each section's name and that block, nothing else.

## The findings note names the landing

Only rewording the note back could fail it; `test_findings_head_is_the_template` keeps the
factory's copy equal to it.

```sh
sed 's/^> //' templates/findings.md | tr '\n' ' ' | tr -s ' ' | grep -q "and its landing's rounds, write their agents' findings into it"
```

## Triage's dangling bullet waits on the push

Only rewording the bullet back could fail it; `intake`'s flag it reads is tested in the suite.

```sh
tr '\n' ' ' < skills/triage/SKILL.md | tr -s ' ' | grep -qF 'An issue an unpushed commit closes (`waits_on_push: true`) is waiting on the push: never offer it again'
```

## Neither spec gate offers "rethink the design"

Only putting the option back in a skill's sample could fail it; `factory.py`'s `spec_question()`
is pinned by `test_start_words_the_spec_question`.

```sh
! grep -n "rethink the design" skills/spec/SKILL.md plugins/factory/skills/spec/SKILL.md plugins/factory/scripts/factory.py && grep -qF '(yes / revise a requirement)`' skills/spec/SKILL.md && grep -qF '(yes / revise a requirement)`' plugins/factory/skills/spec/SKILL.md
```
