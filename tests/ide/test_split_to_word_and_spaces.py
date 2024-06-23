from modelmachine.ide.split_to_word_and_spaces import split_to_word_and_spaces


def test_split():
    assert split_to_word_and_spaces("") == []
    assert split_to_word_and_spaces(" ") == [" "]
    assert split_to_word_and_spaces(" \t ") == [" \t "]
    assert split_to_word_and_spaces("print") == ["print"]
    assert split_to_word_and_spaces(" print \t 10") == [
        " ",
        "print",
        " \t ",
        "10",
    ]
