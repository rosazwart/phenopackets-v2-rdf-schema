'''
    @Description:
    
    Script for generating a YARRRML template for a given directory with SHACL RDF files stored in a TTL file that can be used 
    to generate an RDF dataset that complies to the data structure of GA4GH Phenopacket V2.

    @Author: Rosa Zwart
    @Date: 04-06-2024
'''

import os

import shaclutil.loader as loader
import namespace_provider as namespace_provider
import yamlutil.writer as yaml_writer
import jsonutil.writer as json_writer

DEFAULT_SHACL_FOLDERNAME = 'fdp_shacl'
DEFAULT_SINGLE_FILENAME = None

DEFAULT_NAMESPACE = 'https://example.org/'
DEFAULT_PREFIX = 'ex'

def get_input_value(input_value: str, default_value: str):
    """
        Get user input if a non-empty value is given. Otherwise, return the given default value.

        :param input_value: User input value
        :type input_value: str

        :param default_value: Default value
        :type default_value: str

        :returns: Non-empty user input value or default value
        :rtype: str
    """
    if len(input_value) > 0:
        return input_value
    else:
        return default_value
    
def empty_output_folder():
    """
        Empty the output folder located in the directory of the SHACL2YARRRRML script.
    """
    output_folder_path = os.path.join('shacl2yarrrml', 'output')
    for filename in os.listdir(output_folder_path):
        file_path = os.path.join(output_folder_path, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)

if __name__ == "__main__":
    empty_output_folder()

    shacl_foldername = input(f'Folder containing SHACL files (default: {DEFAULT_SHACL_FOLDERNAME}):')
    shacl_filename = input(f'Specific SHACL file to load (default: {DEFAULT_SINGLE_FILENAME}, all SHACL files found in given folder):')

    new_namespace = input(f'Specify namespace of RDF entities (default: {DEFAULT_NAMESPACE}):')
    new_prefix = input(f'Specify prefix of the namespace (default: {DEFAULT_PREFIX}):')

    rdf_namespace = get_input_value(new_namespace, DEFAULT_NAMESPACE)
    rdf_prefix = get_input_value(new_prefix, DEFAULT_PREFIX)

    shacl_g, shacl_prefixes = loader.load_shacl_files(single_file_name=get_input_value(shacl_filename, DEFAULT_SINGLE_FILENAME), 
                                                      dir_name=get_input_value(shacl_foldername, DEFAULT_SHACL_FOLDERNAME))
    
    shacl_prefixes[rdf_prefix] = rdf_namespace
    namespace_provider.bind_namespaces(g=shacl_g, prefixes=shacl_prefixes)
    
    json_writer.create_template(input_g=shacl_g)
    yaml_writer.create_template(input_g=shacl_g, prefix_dict=shacl_prefixes, rdf_prefix=rdf_prefix, rdf_namespace=rdf_namespace)
