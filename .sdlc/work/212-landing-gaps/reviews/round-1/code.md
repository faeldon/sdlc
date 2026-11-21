VERDICT: PASS

Both outcomes are met and the gate record is green. I found nothing that needs rework.

- **ugrep links (2026-11-20-7):** `--dereference-files` and every prefix of three or more characters after `--` are now refused, with or without `=value`. `-d dereference-recurse` is refused as well, in the `--directories=`, `-ddereference-recurse` and bundled `-rd` forms. The existing GNU and BSD refusals are unchanged, so the list only grows stricter.
- **Readiness refusal (2026-11-20-51):** `test_a_train_names_a_readiness_refusal_as_its_cause` removes `decision.md`, so the train reads the change as unready. It asserts `cause == "refusal"` and that nothing was committed. Mutating the cause to `review` fails the `cause` assertion.
- **Tests:** I ran `tests/test_train.py -k "readiness_refusal or read_only"` and all 74 selected tests pass.

Decisions D1 and D2 are open builder defaults and I accept both: D1 refuses ugrep's program-running and config options, D2 refuses the bare word `dereference-recurse`. Both only tighten the list, which the intent's constraint allows.

## Notes
- NIT: plugins/factory/scripts/landing.py:921: the `--filter`, `--pager` and `--view` refusals match the exact name only, not `--filter-magic-label`. That is harmless and ugrep takes no prefixes, but a comment saying so would help. {docs S low}
- Done well: each new refusal has a paired pass case (`--no-dereference`, `--no-config`, `-d recurse`), so the stricter list doesn't over-refuse.
- Ran: the two named test groups above. I did not run the gate.
