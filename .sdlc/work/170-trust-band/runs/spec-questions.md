
**Open questions resolved**
- *Where does the Claude Code version come from at close: the transcripts, or a new trailer?* Both. Close reads it from the transcripts (each entry's `version`, alongside each assistant entry's `message.model`) and records it in a new trailer, `Sdlc-Runtime`. A trailer is needed because `retro` reads only history (`cmd_retro()`'s docstring) and transcripts don't last. The plugin version comes from the closing script's own manifest (`sdlc.plugin_version()`), and models fall back to the existing `Sdlc-Role` `model=` for older changes.

**Choices made that you may want to change**
- **The Trust band goes into the report's Window section** (`{{window}}`), because the template can't be edited. A host override without `{{window}}` won't show it.
- **Greyed means italics plus "a hint: under half the changes"**, not colour, because GitHub drops styling.
- **"The last window"** is the changes between the two retrospectives before this one. With only one earlier retrospective, it is all history before it.
- **R14 adds one bullet to `skills/retro/SKILL.md`**, telling the passes to read coverage and underneath before trends. The intent didn't ask for it, but O4 isn't met if the skill ignores the figures. Strike R14 to keep the skill untouched, at the cost of the direction not yet resting on these numbers.

**Left for you**
- None from the intent remain open.
