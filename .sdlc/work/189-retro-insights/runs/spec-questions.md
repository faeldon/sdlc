
Resolved:
- **Does each pillar's sub-agent run inside the skill, or through a script command?** Inside the
  skill, through `Agent` (`sdlc:insight`), because core never runs `claude` (AGENTS.md, *The
  factory*: `factory.py agent` is the one place). The script does the mechanical half: it cuts
  each pillar's figures (`retro --insights`), and it parses and renders the answers
  (`retro-commit`).
- **Is the answer shape fixed by the guide or by the script?** By the script (`INSIGHT_FIELDS`,
  the Disposition kinds), because `retro-commit` parses it. The agent's file states it, and a test
  pins the two together.
- **What does a host's extension of the guide look like?** `.sdlc/INSIGHTS.md` (`[docs] insights`),
  read block by block after the guide, the way the review doc is read (R2):
  - `## <Pillar>` with text replaces that pillar's question;
  - `### <Title>` under a pillar adds a question on its figures;
  - any other `##` adds a question on the Tradeoffs figures;
  - an empty heading only places.
- **Nit 2026-11-19-65.** `number()` writes full precision, so the case in the nit (0.174 shown as
  0.17) doesn't happen today. `_trend()` now compares the written value, and a test pins the round
  trip (R12).
- **Nit 2026-11-19-66.** Fixed: minutes keep one decimal place, and REFERENCE.md says so (R13).

Left for you:
- **The AGENTS.md policy edit.** `retro-commit` reads and removes an untracked draft, and the
  report is no longer "from history alone". Approving this spec approves that edit. The other
  option is a fixed path with no draft, which isn't possible, since the answers are judgment, not
  history.
- **Are the insights optional?** As designed, a retrospective can skip them, and the report then
  says `Not answered`. Making them required would make `retro-commit` refuse without a draft, which
  guarantees the section but makes every retrospective pay for seven agent runs.
- **A config key or a fixed path.** `[docs] insights` follows the docs pattern but adds one key to
  the surface the Simplicity pillar counts. A fixed `.sdlc/INSIGHTS.md` path with no key would be
  one less key, but the only docs path a host couldn't move.
- **Whole-minute history.** With R13, the first retrospective after this change may read `up` or
  `down` on the response rows from rounding alone, because the last report wrote whole minutes.
  The other option is to keep whole minutes and only add a note, which avoids that one-time effect
  and keeps the flat-lining.
