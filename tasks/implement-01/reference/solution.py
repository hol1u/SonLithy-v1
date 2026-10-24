def sum_nested(values):
    return sum(sum_nested(value) if isinstance(value, list) else value for value in values)