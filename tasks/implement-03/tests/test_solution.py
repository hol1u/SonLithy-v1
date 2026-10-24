from solution import merge_intervals


def test_merge_intervals():
    assert merge_intervals([[5, 8], [1, 4], [3, 6], [8, 9]]) == [[1, 8], [8, 9]]
    assert merge_intervals([]) == []
    assert merge_intervals([[2, 3]]) == [[2, 3]]