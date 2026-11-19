
**Resolved**

- *What marks a nit taken in?* A `Nits taken in:` line in the intent's Approach (Tier 1) or the
  spec's Requirements (Tier 2), read only within those sections, in the forms R2 lists. A
  section of its own is rejected (it's a new template heading, so a breaking setup change), and
  so is review confirmation (the intent's constraint forbids it). The line matches what the
  intent says 173's Approach already does. I couldn't read 173's folder, which close has removed,
  so the exact spelling is taken from the intent; the match ignores case and allows a list item
  or a bold lead to cover the variants.
- *Does core `/sdlc:ship` need the same marker?* Not to read it. Ship proposes each retirement
  from the nits its Step 0 lists, for the person's yes. Both tools write the marker the same way,
  because the shared intent and spec skills tell them to (R4).
- *How does the builder say a fix is already made?* With a line the script reads (`FIX: ALREADY
  MADE`, read by `opening()`) and a `## Evidence` section `read_evidence()` accepts, on top of an
  empty diff outside the folder. An empty diff alone is not enough.

**Left for the person**

- *Changes already open.* 174, 175 and 176 take nits in. Their Tier 2 intents name them in the
  Problem, and their specs aren't drafted yet. If those specs are drafted before this change
  lands, they will name the ids in Requirements without the marker, and their landings will
  retire nothing: the nits stay open and need retiring by hand. Your options: accept that, add a
  `Nits taken in:` line to each of those specs when they are drafted, or land this change first.
- *Spelling of the answer line.* `FIX: ALREADY MADE` follows the `VERDICT:`/`DECISION:` style.
  Any wording works the same, as long as the prompt and `FIX_RE` agree.
