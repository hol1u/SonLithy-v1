from solution import binary_search


def test_binary_search():
    assert binary_search([1, 2, 2, 2, 5], 2) == 1
    assert binary_search([1, 3, 7], 4) == -1
    assert binary_search([], 4) == -1