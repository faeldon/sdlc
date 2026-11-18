# Ship — undone items

`preflight`'s `branches` names this file when its `undone` part lists unticked `- [ ]` lines in the
change's `notes.md`.

## Step 4

**Undone items.** For each item Step 0 listed, propose one of these dispositions:

- **carry it forward:** a new seed, filed in `.sdlc/work/inbox.md` when the change closes, with a
  short title of its own;
- **file it as a bug:** only for an item starting `pre-existing:` (a fault a reviewer found in code
  the change didn't touch, as a factory run carries one): proposed in the shape this step gives a
  Pre-existing finding, `## [<id>] [bug] <title>` with its `Severity:` (one of the process doc's
  words) and `Paths:` lines, and counted in the question's `--bugs`;
- **drop it:** with a one-line reason (done after all, superseded, not worth doing).

There is no other option, such as keeping it as an open question in `intent.md`: a shipped intent
is read no more than its notes. An undone item doesn't block shipping; a known gap can ship once
it's written down somewhere that gets read. Put the dispositions in the commit message, after the
body, as a `Carried forward:` and a `Dropped:` paragraph, one line per item. Leave out a paragraph
that has nothing in it; an item filed as a bug is in neither, since the bug is named with the
others. Each carried seed and each bug takes an id from Step 4's `next-entry` call.

## Step 6

First, the undone items, exactly as approved:

- **Carried:** add each seed to the change's `entries.md` (in `SKILL.md`'s shape) as
  `## [<id>] [idea] <its title>`, with the id Step 4 took for it; close files it in the register.
  Its body says what is left to do and points at
  `.sdlc/work/NNN-slug/notes.md` in this change's commit. Then tick the item in place:
  `- [x] <text> → seed: <id>`.
- **Filed as a bug:** add it to `entries.md` with the pre-existing bugs, as Step 6 files those, with the id
  Step 4 took for it, then tick it: `- [x] <text> → bug: <id>`.
- **Dropped:** tick it as `- [x] <text> → dropped: <the reason>`.
