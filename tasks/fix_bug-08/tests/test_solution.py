from solution import intersection_sorted


def test_intersection_sorted():
    assert intersection_sorted([4, 1, 2, 2], [2, 4, 4]) == [2, 4]
    assert intersection_sorted([], [1]) == []