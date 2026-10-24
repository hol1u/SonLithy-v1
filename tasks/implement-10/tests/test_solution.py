import pytest
from solution import parse_ranges


def test_parse_ranges():
    assert parse_ranges("1-3, 5, 7-8") == [1, 2, 3, 5, 7, 8]
    assert parse_ranges("") == []
    with pytest.raises(ValueError):
        parse_ranges("3-1")
    with pytest.raises(ValueError):
        parse_ranges("2,x")