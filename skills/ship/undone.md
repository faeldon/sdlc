# Ship — undone items

`preflight`'s `branches` names this file when its `undone` part lists unticked `- [ ]` lines in the
change's `notes.md`.

## Step 4

**Undone items.** For each item Step 0 listed, propose one of two dispositions:

- **carry it forward:** a new `.sdlc/work/inbox.md` seed, with a short title of its own;
- **drop it:** with a one-line reason (done after all, superseded, not worth doing).

There is no third option, such as keeping it as an open question in `intent.md`: a shipped intent
is read no more than its notes. An undone item doesn't block shipping; a known gap can ship once
it's written down somewhere that gets read. Put the dispositions in the commit message, after the
body, as a `Carried forward:` and a `Dropped:` paragraph, one line per item. Leave out a paragraph
that has nothing in it. Each carried seed takes an id from Step 4's `next-entry` call.

## Step 6

First, the undone items, exactly as approved:

- **Carried:** append each seed to the register as `## [<id>] [idea] <its title>`, with the id
  Step 4 took for it. If it doesn't exist, `Write` it at that path first from
  `templates["inbox.md"]` in `config`, as it is, then append. Its body says what is left to do and points at
  `.sdlc/work/NNN-slug/notes.md` in this change's commit. Then tick the item in place:
  `- [x] <text> → seed: <id>`.
- **Dropped:** tick it as `- [x] <text> → dropped: <the reason>`.
