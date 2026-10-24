from solution import rotate_list


def test_rotate_list():
    assert rotate_list([1, 2, 3, 4], 1) == [4, 1, 2, 3]
    assert rotate_list([1, 2, 3], -1) == [2, 3, 1]
    assert rotate_list([], 5) == []