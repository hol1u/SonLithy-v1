def chunked(values, size):
    if size <= 0:
        raise ValueError("size must be positive")
    return [list(values[index:index + size]) for index in range(0, len(values), size)]