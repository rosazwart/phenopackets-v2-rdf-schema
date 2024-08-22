import os
import rdflib
import re

def fill_declared_prefixes(prefix_dict: dict, file_path: str):
    """
        Read out the SHACL files and use regex to get all declared namespaces and their prefixes.

        :param prefix_dict: Dictionary of already declared namespaces (standard namespaces always included no matter the model)
        :datatype prefix_dict: dict

        :param file_path: Path to SHACL file
        :datatype file_path: str
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    prefix_pattern = r"@prefix\s+([a-zA-Z0-9-_]+):\s*<([^>]+)>"
    declared_prefixes = re.findall(prefix_pattern, content)
    for prefix, namespace in declared_prefixes:
        prefix_dict[prefix] = namespace

def load_shacl_files(dir_name: str, single_file_name: str | None = None):
    """
        Load SHACL files from a given directory in the current working directory. If a filename is specified, only load this SHACL file from the directory. 

        :param dir_name: Name of directory found in current working directory
        :type dir_name: str

        :param single_file_name: Name of specific SHACL file that needs to be loaded from the directory
        :type single_file_name: str | None
        :default single_file_name: None

        :returns: RDF graph representing the content of the SHACL file(s) and a dictionary with all declared prefixes
        :rtype: rdflib.Graph, dict
    """
    curr_wdir = os.getcwd()

    g = rdflib.Graph()
    prefix_dict = {}

    for file_name in os.listdir(dir_name):
        file_path = os.path.join(curr_wdir, dir_name, file_name)
        if os.path.isfile(file_path) and (single_file_name is None or file_name == single_file_name):
            print('Add SHACL shapes from', file_name)
            g.parse(file_path)

            fill_declared_prefixes(prefix_dict, file_path)

    print('RDF graph with SHACL shapes created from directory', os.path.join(curr_wdir, dir_name))
    print(f'Declared prefixes are: {prefix_dict}')

    return g, prefix_dict