import pytest
from solution import fibonacci


def test_fibonacci():
    assert [fibonacci(n) for n in range(8)] == [0, 1, 1, 2, 3, 5, 8, 13]
    with pytest.raises(ValueError):
        fibonacci(-1)