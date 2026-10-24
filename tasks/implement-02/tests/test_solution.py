from solution import normalize_whitespace


def test_whitespace_normalization():
    assert normalize_whitespace("  a\t b\n c ") == "a b c"
    assert normalize_whitespace("") == ""