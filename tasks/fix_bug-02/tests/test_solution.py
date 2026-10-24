import pytest
from solution import median


def test_median():
    assert median([9, 1, 5]) == 5
    assert median([8, 2, 4, 6]) == 5
    with pytest.raises(ValueError):
        median([])