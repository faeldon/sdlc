
**Changed in this revision**

- **jq and awk are now reads** when they don't redirect or write (R1's table and the Design). jq is a read under the shell rules alone, since it can't write by itself. awk is a read unless it loads its program from a file or an extension, or its program pipes, calls `system`, or redirects a `print`. A substitution check now looks only outside single quotes, so a quoted program's `$(` or `$` is safe.
- **R5 uses rebuilt fixtures.** They come from the commands bug 2026-11-17-90 quotes, and the test's docstring says so. The open question about recovering 119's replies from history is gone.

**Resolved**

- *Exempt reads in the script, or tighten the prompt?* In the script. The prompt already asks for exits on reads and still failed (`reviewer-behaviour.md:68`; 119's reply and its mend). Which commands count as reads is the closed allowlist in Design. A pipeline is judged stage by stage: a read only if every stage is a read and nothing redirects to a file. A read is excused only when it shows output (R3).
- *Does the builder's report get the same exemption?* Yes. One parser serves both roles (`read_evidence()`, called from `loop_state()` and `land_verdict()`), and the builder's gate and test runs never qualify as reads (R4, R6).
- *The board's and `status`'s copies of the evidence parsing:* none exist in `scripts/board.py` or `scripts/sdlc.py`, so the constraint is met by adding none. The problem strings the board's fixtures hold are kept word for word.
- *R5's fixtures:* rebuilt from bug 2026-11-17-90's quoted commands, as you approved.

**Left for the person**

- None. Two smaller notes:
  - `gawk`, `mawk` and `uniq` stay non-reads. Adding one later is a row in R1's table.
  - In awk, a `>` inside a `print` is refused even when it's only a comparison, such as `print ($1 > 2)`. That costs at most one mend.
