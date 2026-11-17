VERDICT: PASS

## Notes

Fine. The share link is built by `share_url()` and checked against **every** saved draft, as
[the spec](../../spec.md) asks; the [link format](https://example.com/drafts) is unchanged.

### Checked

- [x] A saved draft gets a link.
- [x] An unsaved draft gets none.
- [ ] A revoked link answers 410 (left to round 2).

| Requirement | Test | Result |
| --- | --- | --- |
| R1 | `test_a_saved_draft_is_shared` | pass |
| R2 | `test_an_unsaved_draft_is_not` | pass |

```python
def share_url(draft: Draft) -> str:
    return f"https://example.com/drafts/{draft.id}?token={draft.token}&expires={draft.expires_at.isoformat()}"
```

> A note for the next round: the token's length is the spec's, not the library's default.
