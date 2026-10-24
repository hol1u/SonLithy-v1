from solution import flatten_dict


def test_flatten_dict():
    assert flatten_dict({"a": {"b": 2}, "c": 3, "empty": {}}) == {"a.b": 2, "c": 3}
    assert flatten_dict({}) == {}