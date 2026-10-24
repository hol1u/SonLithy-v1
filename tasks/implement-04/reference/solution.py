def rotate_list(values, k):
    if not values:
        return []
    shift = k % len(values)
    return list(values[-shift:] + values[:-shift]) if shift else list(values)