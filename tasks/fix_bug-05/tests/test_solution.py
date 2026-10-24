import pytest
from solution import chunked


def test_chunked():
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunked([], 2) == []
    with pytest.raises(ValueError):
        chunked([1], 0)