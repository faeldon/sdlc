import drafts


def test_a_renamed_draft_keeps_its_text_under_the_new_title() -> None:
    drafts.save("Monday", "Notes for the week")
    assert drafts.rename("Monday", "Week one")
    assert drafts.titles() == ["Week one"] and drafts.DRAFTS["Week one"] == "Notes for the week"


def test_a_rename_onto_a_taken_title_changes_nothing() -> None:
    drafts.DRAFTS.clear()
    drafts.save("a", "1")
    drafts.save("b", "2")
    assert not drafts.rename("a", "b")
    assert drafts.DRAFTS == {"a": "1", "b": "2"}
