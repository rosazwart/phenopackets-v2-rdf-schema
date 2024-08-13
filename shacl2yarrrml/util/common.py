def from_nodeshape_name_to_name(nodeshape_name: str):
    """
        Get label from nodeshape name.

        :param nodeshape_name: Name of nodeshape
        :datatype nodeshape_name: str

        :returns: Formatted name of nodeshape
        :rtype: str
    """
    return nodeshape_name.lower().replace('shape', '')

def from_property_path_to_name(property_path: str):
    """
        Get label from property path name.

        :param property_path: Property path name
        :datatype property_path: str

        :returns: Formatted name of property path
        :rtype: str
    """
    return property_path.replace(':', '_')

def add_to_dict_of_counters(dict_values: dict, key, add_number: int = 1):
    """
        Add entry to dictionary storing counts per key value.

        :param dict_values: Dictionary storing counts
        :datatype dict_values: dict

        :param key: Value of the key of which the counter value needs to be modified
        :datatype key: any

        :param add_number: Value that needs to be added to the counter value
        :datatype add_number: int
    """
    if key in dict_values:
        dict_values[key] += add_number
    else:
        dict_values[key] = add_number
