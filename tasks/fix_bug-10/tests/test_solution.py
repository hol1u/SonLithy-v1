import pytest
from solution import percentile


def test_percentile():
    assert percentile([30, 10, 20], 50) == 20
    assert percentile([0, 10], 25) == 2.5
    assert percentile([3], 100) == 3
    with pytest.raises(ValueError):
        percentile([], 50)
    with pytest.raises(ValueError):
        percentile([1], 101)