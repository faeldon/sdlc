VERDICT: PASS

## Notes

This change adds timing only. It writes UTC times, whole minutes and a fixed source word, and it sends nothing out. No new dependency, secret, network call, shell call or destructive step comes in. `closing.py` is in `[review] sensitive`, so I read all of its diff.

**Trust boundaries, checked with STRIDE:**
- **The change's own `opened:` frontmatter line.** It is read as text through `frontmatter_list` and parsed with `strptime` against a fixed format. If a value doesn't fit, the coverage gains `lead=bad-opened`; nothing raises and nothing is written over. A change could backdate its own `opened:` and inflate its lead time. That is tampering with a metric, not with the system. The cost is a skewed retro figure, which is the same trust a change already gets for every other line in its folder.
- **The run files committed on the branch (`runs/costs.jsonl`, `runs/land-times.jsonl`).** These are read with `git show` using fixed argument lists, and `folder` and `branch` are close's own values. Each line is parsed with `json.loads`, and anything that isn't a dict is skipped. Times are parsed with `strptime`, which catches `TypeError` and `ValueError`. The `role` value is only compared, never written out. Nothing from these files reaches a trailer except numbers made by `_minutes`.
- **The trailer written into the `Close` commit message.** `lead_trailer` writes `_minutes` integers and `source=_word(...)`, and the source is always one of three words set in the code. A crafted run file can't inject a newline or a forged `Sdlc-*` trailer through it.
- **Reading the trailer back in retro.** `lead_view` only counts values that are `int` (`isinstance(..., int)`), so a hand-written commit with a malformed `Sdlc-Lead` moves no figure. The tier and mode strings in the report table come from existing sources, and the report is a local markdown file.
- **Denial of service, and "measuring never refuses".** `_lead_marks` and the arithmetic run inside a broad `except Exception`, which records `lead=failed`. A malformed run file or git date therefore can't make close fail. The cost of reading the run files grows with their size, the same as the transcripts close already reads.
- **Information disclosure.** The new `started` and `ended` fields in `costs.jsonl` and the new `since` field in `land-times.jsonl` are timestamps only. No prompts, replies, paths or user names are added. This meets the intent's "nothing local in the trailers" rule.
- **`_with_opened` in `new`.** It inserts one line into the template's frontmatter and keeps every other line as it was. The template may be the host's own, and it is already trusted.

**Things done well:**
- The parse is strict and fails closed into a coverage word, never into a 0.
- A dropped change gets no lead line.
- `metrics.py` stays pure, with no subprocess or import added.
- `stamp_shipped` is untouched.

**What I checked:**
- I read `intent.md`, `decisions.md`, the full diff of `scripts/`, `plugins/factory/scripts/factory.py` and `docs/REFERENCE.md`, and the gate record `build/round-1.gate.md`.
- I traced how the `Sdlc-Lead` trailer is written (`_pairs`, `_word`, `_minutes`) and read back (retro's `lead_view`).
- I ran nothing beyond reading git and files.

**Decisions D1–D3 have no security weight**, so I raise no decision.

- NIT: scripts/closing.py:475: the broad `except Exception` also hides programming errors as `lead=failed`. That fits "never refuses", but it could log the exception's type name to stderr so a regression is visible {robustness S low}
