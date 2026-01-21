from utils.deck_utils import format_deck_label, make_deck_key, split_deck_key


def test_make_deck_key_with_single_monster():
    assert make_deck_key("Veromos", "", "") == "Veromos||"


def test_make_deck_key_with_two_monsters():
    assert make_deck_key("Veromos", "Lushen", "") == "Veromos|Lushen|"
    assert make_deck_key("Veromos", "", "Lushen") == "Veromos|Lushen|"


def test_make_deck_key_with_three_monsters_sorted():
    assert make_deck_key("Veromos", "Zaiross", "Lushen") == "Veromos|Lushen|Zaiross"


def test_split_deck_key_padding():
    assert split_deck_key("Veromos|Lushen|") == ["Veromos", "Lushen", ""]
    assert split_deck_key("Veromos||") == ["Veromos", "", ""]


def test_format_deck_label_with_placeholders():
    assert format_deck_label(["Veromos", "", ""], placeholder="-") == "Veromos / - / -"
    assert format_deck_label(["Veromos", "Lushen", ""], placeholder="-") == "Veromos / Lushen / -"
