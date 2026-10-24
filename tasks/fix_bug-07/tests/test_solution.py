from solution import is_palindrome


def test_palindrome_normalization():
    assert is_palindrome("A man, a plan, a canal: Panama!")
    assert is_palindrome("...")
    assert not is_palindrome("Python")