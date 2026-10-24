from solution import top_k_words


def test_top_k_words():
    assert top_k_words("Pear apple pear, APPLE pear!", 2) == ["pear", "apple"]
    assert top_k_words("b a c", 3) == ["a", "b", "c"]
    assert top_k_words("a", 0) == []