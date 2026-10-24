def longest_unique_substring(text):
    last_seen = {}
    start = best = 0
    for index, char in enumerate(text):
        if char in last_seen and last_seen[char] >= start:
            start = last_seen[char] + 1
        last_seen[char] = index
        best = max(best, index - start + 1)
    return best