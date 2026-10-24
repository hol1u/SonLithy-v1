def percentile(values, p):
    return sorted(values)[int(len(values) * p / 100)]