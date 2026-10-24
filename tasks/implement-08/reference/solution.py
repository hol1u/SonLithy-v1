def flatten_dict(data):
    result = {}

    def visit(mapping, prefix):
        for key, value in mapping.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                visit(value, path)
            else:
                result[path] = value

    visit(data, "")
    return result