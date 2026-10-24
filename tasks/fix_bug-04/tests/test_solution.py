from solution import dedupe_preserving_order


def test_dedupe_preserves_order():
    assert dedupe_preserving_order([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert dedupe_preserving_order([]) == []