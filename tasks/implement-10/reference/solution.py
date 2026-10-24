import re


def parse_ranges(spec):
    if not spec.strip():
        return []
    result = []
    for item in spec.split(","):
        match = re.fullmatch(r"\s*(-?\d+)\s*(?:-\s*(-?\d+)\s*)?", item)
        if not match:
            raise ValueError(f"Invalid range item: {item}")
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) is not None else start
        if end < start:
            raise ValueError("Range end must not be less than start")
        result.extend(range(start, end + 1))
    return result