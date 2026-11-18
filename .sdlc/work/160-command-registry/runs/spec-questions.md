
**Open questions resolved**

- **The registry's shape.** A `@command(name, about, *specs)` decorator on a small `cli_<name>` adapter placed beside each handler, with the module-level `HELP_ORDER` tuple pinning today's top-level order. A central table only moves the conflict. Decorating `cmd_*` directly would change signatures or break live stand-ins. Help order taken from the file would reshuffle `--help`, which the intent forbids. A new command needs no edit to `HELP_ORDER`, so two parallel new commands don't conflict.
- **Whether `closing.py` and `landing.py` register their own commands.** No: the scripts register them on the modules' behalf. The code settles this: `test_the_modules_read_nothing_while_loading` forbids a load-time decorator in those modules, and their binding is unset while they load. The sensitive modules stay out of the diff. The same applies to `retro.py` and `board.py`.
- **Whether `READ_ONLY` and `ALLOW_RULES` are derived from the registry.** No: they are kept as they are and checked against the registry (R9). A derived list would change `ALLOW_RULES`' order, which setup writes into a host's settings and `readiness` prints, so it isn't a pure move. `OWN_SCRIPT_CMDS` gets the same treatment.

**Left for you**

- **`HELP_ORDER` versus accepting a new help order.** Keeping `HELP_ORDER` meets the intent's byte-identical bar. Dropping it would let the help follow file order, with no list at all, at the cost of a one-time reshuffle of the top-level `--help`. The spec assumes you keep it.
- **A line in `docs/CONTRIBUTING.md` on how to add a command.** I left this out because the intent didn't list docs. Adding it would cost one doc edit in this change.
