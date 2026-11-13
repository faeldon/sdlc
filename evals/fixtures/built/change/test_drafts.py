import drafts


def test_a_saved_draft_reopens_with_its_text() -> None:
    drafts.save("Monday", "Notes for the week")
    assert drafts.reopen("Monday") == "Notes for the week"


def test_a_title_never_saved_reopens_nothing() -> None:
    assert drafts.reopen("Never saved") is None
