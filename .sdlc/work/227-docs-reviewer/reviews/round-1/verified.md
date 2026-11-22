- KEPT: code: C1: skills/ship/docs.md:28: it says `sdlc.py ship` refuses any diff the docs pass applies to when the note lacks a `Docs review:` line, but `cmd_ship` asks for that line only when `findings.md` exists (sdlc.py:4187).
- The other files make no such claim. `skills/ship/SKILL.md:231`, `docs/REFERENCE.md:325` and `plugins/factory/README.md:389` don't mention the refusal, so only `docs.md` needs rewording.
- D1 stays open for the person, and the wording has to follow whichever way it is answered.

## Notes
I ran nothing. I read `docs.md`, `sdlc.py` around line 4187, and grepped `SKILL.md`, `REFERENCE.md` and the factory `README.md`.
