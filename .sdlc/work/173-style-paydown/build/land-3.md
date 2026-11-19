I resolved `AGENTS.md`. I ran no tests, because the only file changed is a docs file. No conflict markers were left in it.

**What conflicted.** The "Modules loaded by path" paragraph. The base had changed the sentence about who reaches `factory_records.py` from "the board and close" to "the board, close and retro". 173 re-wrapped the whole paragraph to 100 columns and still had the old wording.

**What I kept.**
- **From the base (172):** the new content, "the board, close and retro reach `factory_records.py` through their binding".
- **From 173:** the 100-column re-wrap of the paragraph, so its line-width nit stays fixed.
- **How I combined them:** I refilled the tail of the paragraph so no line passes 100 columns. That tail is the sentence from "`closing.py` and `landing.py` are apart" to the end.
- **Other paragraphs:** 173's re-wraps of the board, factory and push paragraphs merged cleanly. I didn't touch them.

I couldn't confirm the width check for the whole file. My `awk 'length>100'` check counts bytes, so it also lists one line of the opening paragraph that contains `→` arrows. That line isn't part of 173's change.

I noticed nothing else to report.

## Evidence

$ grep -n '<<<<<<<\|>>>>>>>\|^=======' AGENTS.md
exit: 1

$ awk 'length>100' AGENTS.md
stages (intent → spec → plan → build → ship → close), with a human gate at every stage that
exit: 0

$ grep -c 'and close reach' AGENTS.md
0
exit: 1
