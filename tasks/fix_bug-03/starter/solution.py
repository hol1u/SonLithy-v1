def binary_search(values, target):
    middle = len(values) // 2
    return middle if values[middle] == target else -1