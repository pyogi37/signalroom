from signalroom.segmentation import numbered, segment, speakers


def test_segments_speaker_lines_and_skips_blanks():
    text = "Operations lead: We find out too late.\n\n[04:18] IT architect: The gateway stays.\n(12:06) Sponsor - keep this short: Success means faster mornings.\nJust a stray line\n"
    items = segment(text)
    assert [item.line for item in items] == [1, 2, 3, 4]
    assert items[0].speaker == "Operations lead" and items[0].text == "We find out too late."
    assert items[1].speaker == "IT architect" and items[1].text == "The gateway stays."
    assert items[2].speaker == "Sponsor - keep this short"
    assert items[3].speaker == "Unattributed" and items[3].text == "Just a stray line"


def test_note_labels_are_not_speakers():
    items = segment("Note: the gateway is staying.\nOperations lead: agreed.")
    assert items[0].speaker == "Unattributed"
    assert items[1].speaker == "Operations lead"


def test_roster_counts_lines_per_speaker():
    items = segment("A: one\nB: two\nA: three")
    assert [(item.speaker, item.lines) for item in speakers(items)] == [("A", 2), ("B", 1)]


def test_numbered_rendering_is_stable():
    items = segment("A: one\nB: two")
    assert numbered(items) == "[L01] A: one\n[L02] B: two"
