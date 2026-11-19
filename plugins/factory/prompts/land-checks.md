# land-checks

> The factory fills this file and sends it to the agent word for word: `factory.py` picks each
> `## ` part a prompt needs, fills its `${name}` placeholders (`$$` is a literal `$`), and joins the
> parts. Each part is one line, never wrapped: its newlines are the prompt's. The title and this
> note are never sent.

## main

The person approved this change's acceptance checks word for word when they said yes to its landing, and its `checks.md` has changed since. A train runs a change's acceptance checks unattended only when you judge every added or edited command harmless and the script's read-only list passes it too; your word alone never runs one. The acceptance checks they approved: ${approved}. Those it holds now: ${current}. Added or edited: ${changed}. Removed, which run nothing: ${removed}. Read each added or edited command, and the files it reads: does any of them write or delete a file, reach the network, read outside the checkout, read a secret (a key, a token, a .env file) into its output, or do anything but check the change? Edit nothing and run nothing. Open your reply with `CHECKS: HARMLESS` or `CHECKS: ESCALATE` alone on its first line, then say why, command by command.
