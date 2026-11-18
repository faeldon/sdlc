I added a `## Hosts` section to `docs/RETRO-SCORECARD.md`, between *Insights* and *Seeds to build it*. Nothing else changed and I ran no git command. Both acceptance checks and `test_nothing_local` still pass; I didn't rerun the full gate for this doc-only edit.

It covers the three Hosts items in `notes.md`:
- **How the scorecard reaches hosts:** once S14 and S15 build it, the numbers go in core `sdlc.py retro` and the page in `templates/retro.md`, which a host can override in `.sdlc/templates/`. The synthesis questions go in a `guide/` file a host extends, and the metrics' meanings in `docs/REFERENCE.md`'s *Retrospectives*. This doc stays the design reference. In a host, Simplicity means the process's own overhead and workarounds there, and the structural debt index comes from the host's own `retro.indicators`.
- **Lead time's start time:** a host on local numbering has no GitHub issue, and `created:` holds only a date, so S1 has `new` record a timestamp.
- **What a host's scorecard leaves out:** nothing about the skills' cases. A host with no factory gets the by-hand view, saying "no factory changes" rather than showing zeros.

## Evidence

$ uv run --quiet --script scripts/sdlc.py accept 159 | grep -E '"passed"'
      "passed": true,
      "passed": true,
  "passed": true,
exit: 0

$ uv run --group dev pytest -q tests/test_nothing_local.py
8 passed in 0.50s
exit: 0
