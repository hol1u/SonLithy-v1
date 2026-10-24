from solution import group_anagrams


def test_group_anagrams():
    assert group_anagrams(["eat", "Tea", "tan", "ate", "nat"]) == [["eat", "Tea", "ate"], ["tan", "nat"]]
    assert group_anagrams([]) == []