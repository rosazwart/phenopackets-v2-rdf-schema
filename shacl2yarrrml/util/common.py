def from_nodeshape_name_to_name(nodeshape_name: str):
    return nodeshape_name.lower().replace('shape', '')

def add_to_dict_of_counters(dict_values: dict, key, add_number: int = 1):
    if key in dict_values:
        dict_values[key] += add_number
    else:
        dict_values[key] = add_number
