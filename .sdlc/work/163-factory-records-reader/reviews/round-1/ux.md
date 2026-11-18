VERDICT: PASS

This change moves code and is meant to leave the board's output unchanged. I found nothing that gets in the person's way.

## Notes

- **What I read:** both screenshots (1280×800 and 390×844), `intent.md`, and `scripts/board.py`'s reads through `sdlc.factory_records`. The change touches no markup, labels or styles.
- **Desktop:** the columns Planned, Designing, Building, Ready, Landing and Needs You all render. Each card shows its stop reason, its "needs you" line and its `next:` command. Cards where the factory stopped or is waiting on a decision (006, 007) are red, so they stand out.
- **Phone width:** the board becomes a single column, and only the Needs You column showed in the screenshot. The stop reasons and the `next:` commands wrap and can be read.
- **States I couldn't see:** empty, loading and error states for the board. The change doesn't alter them, and the outcome requires byte-identical output. I didn't check that with the tests.
- **Smaller finding:** nothing for this change, and no PREEXISTING items.
- **Done well:** the board now reads every record through `sdlc.factory_records`, so a card's stop text and `status`'s text come from one reader and can't differ. Card wording and the `next:` commands are unchanged.
