import pytest
from solution import clamp


def test_clamp():
    assert clamp(5, 0, 4) == 4
    assert clamp(-2, 0, 4) == 0
    assert clamp(2, 0, 4) == 2
    with pytest.raises(ValueError):
        clamp(2, 4, 0)