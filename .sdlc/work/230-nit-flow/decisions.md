# Decisions

- [x] D1 (builder round 1, default): Name core's copy of the factory's `_section()` `_nit_section()`? Going ahead with it unless told otherwise. → settled by the approver: `_nit_section()` is a naming choice inside a pinned copy of the factory's reader. R9 asks for a copy and says it never imports, the R9 test pins both readers agreeing, and the code review found no clash with core's `_section()`.
  - OPTION: `_nit_section()` — no clash with core's existing `_section()`, which ignores case and skips code fences; the R9 test pins that both readers agree
  - OPTION: change core's `_section()` to the factory's shape — one name, but it changes what core's other callers get back
  - WHY: R9 asks for an exact copy, and core's `_section()` behaves differently
- [x] D2 (builder round 1, default): Word the new `earlier` review part as "Nits you raised in round ${before}: ${nits}; raise again, word for word with its weights, any that are still true." Going ahead with it unless told otherwise. → settled by the approver: the wording is internal to the new `review` part (R4). The spec fixes its behaviour, the `review-earlier` prompt fixture pins the wording, and `test_a_review_names_its_roles_earlier_nits` covers its behaviour, including the restart case that motivated naming the round.
  - OPTION: name the round (`before nits`) — the reviewer knows which of its replies the nits came from
  - OPTION: `nits` alone — one placeholder, as the spec's "its placeholder" reads
  - WHY: after a restart, the earlier round isn't the one just before, so it is worth saying
