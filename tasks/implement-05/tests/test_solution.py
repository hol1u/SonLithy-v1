from solution import is_balanced


def test_balanced_delimiters():
    assert is_balanced("f(a[0], {b: 1})")
    assert is_balanced("no delimiters")
    assert not is_balanced("([)]")
    assert not is_balanced("{")