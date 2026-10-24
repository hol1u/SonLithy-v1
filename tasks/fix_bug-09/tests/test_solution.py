from solution import word_count


def test_word_count():
    assert word_count("one two one") == 3
    assert word_count("  \n ") == 0