# Decisions

- [x] D1 (builder round 1, default): Should ship's UI skip reason point a person at `factory.py shots` when there are no screenshots? Going ahead with no pointer unless told otherwise. → decided: the assumed default, confirmed
  - OPTION: no pointer — ship never names a command that starts a dev server; a person has to know the factory's command to get the UI review
  - OPTION: name `factory.py shots <NNN> --round 1 --role ui|ux` in `passes.ui.why` when sdlc-factory is enabled — the UI review is one step away; ship's text then points at a command that starts a server
  - WHY: the spec leaves how a hand-built change gets screenshots open, and the constraint that ship never starts a server argues for not steering toward one
