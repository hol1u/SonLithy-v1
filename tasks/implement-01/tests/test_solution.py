from solution import sum_nested


def test_nested_sum():
    assert sum_nested([1, [2, [3]], []]) == 6
    assert sum_nested([]) == 0
    assert sum_nested([[-4], 4]) == 0