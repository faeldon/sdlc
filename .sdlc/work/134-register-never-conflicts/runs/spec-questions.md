
Open questions resolved:
- **Which way?** (a), done inside the `Close` commit: entries are held in the change's folder, and close files and retires them in the commit that removes the folder. Not (b) or (c): union merging can bring back a deleted seed, and it would need a line in every host's `.gitattributes`. See *Alternatives rejected*.
- **A landing that commits but stops before close?** The entries are held on the branch and filed only once the change is on the base, by close. A shipped change can't be dropped (`cmd_drop()` refuses `stage: shipped`), so nothing held is lost. R12 covers a dropped change.
- **Does union merging survive a deleted entry, and does it reach hosts?** No to both: in a conflict it keeps both sides' lines, so the seed comes back, and hosts would each need the attribute line. Not used.
- **Does ship by hand change the same way as the landing?** Yes. Both write `entries.md`, `sdlc.py ship` no longer deletes the seed, and the same close files them (R1–R4, R13).

Left for you:
- **The two policy edits under Contracts touched:** a `Close` commit now also writes the register, and close joins `inbox-commit` as code that commits the register (never on its own). Say yes to both, or this design doesn't hold.
- **R10:** a shipped but unclosed change keeps claiming its seed. This reverses `test_a_shipped_change_no_longer_claims_its_seed`. It follows from the seed staying on the base until close. If you'd rather it didn't, a seed could be taken twice in that window, and close would just report its retirement as `gone`.
- **R12:** drop refusing while `entries.md` holds entries. The alternative is dropping and letting those unfiled entries go, which only happens if ship's Step 6 wrote them and the person then dropped instead of shipping.
