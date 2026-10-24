import re
from collections import Counter


def top_k_words(text, k):
    if k <= 0:
        return []
    counts = Counter(re.findall(r"[a-z0-9']+", text.lower()))
    return sorted(counts, key=lambda word: (-counts[word], word))[:k]