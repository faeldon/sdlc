
Resolved from the code:

- **Which signals first, and what each informs:** the table in Design. Everything there is read from trailers and files the plugin already writes, so its readers exist.
- **Transcripts:** a change's sessions are already read at close by `metrics.read_events()`, which keeps text, paths and session ids out, and their counts are in the trailers this change reads. The sessions outside a change are left `unmeasured`, and raw transcripts are not read in this change.
- **Insight agents or the evidence script:** the agents get host figures, so the reading must be `retro.py`'s own. 189 R4 bars evidence output from reaching an agent, and the report never renders evidence.
- **Older hosts:** read where the trailers exist. A missing one is unmeasured, through `metrics_summary()`'s existing `uncaptured` rule. An intent under the old `work/` gives tier `unknown`, with no new `HISTORY_WORK` reader (R8).
- **Weighing a biased sample:** not weighed by the script. The figures stay apart (R12), the report and every bundle carry the host count and a sample note (R6, R11, R15), and the judgment is the insight agents' and the person's.
- **M13:** this makes it measurable. `hosts.all.by_way.factory` and `read.read` let the direction pass judge G7 and M13 by a host factory landing (R14). The milestone rule itself is unchanged.
- **Where discovery is said, and how to add or exclude:** `retro` gives the count only. `sdlc.py hosts`, run by the person, shows paths and the line to append. `!path` excludes a repo for good. `status` doesn't say it.

Left for the person:

- **Plugin feature or this repo's alone.** The spec gates host reading on the plugin's own repo, with no config key.
  - Making it a feature (a `retro.hosts` key, or reading `.sdlc/hosts.local` in any repo) would let a host with its own projects read them, at the cost of a new key, a setup question and every host's confidentiality call.
- **The `## Hosts` heading in every host's report.** It goes in `templates/retro.md` (an `irreversible` path), rendering one line in a host.
  - The other choice is to keep the template unchanged and render host figures only into this repo's report through an own-repo override of the template. That has no host-visible change, but it is a second copy of the template to keep in step.
- **`busiest` as a separate figure.** It is unnamed, but it is one host's numbers in a public report.
  - Dropping it keeps only pooled figures, which are safer but lose the intent's "15 in the busiest host" comparison.
- **The window for host figures.** It is the time since this repo's last retrospective, with all-time beside it.
  - All-time alone would be simpler, but couldn't show a trend.
