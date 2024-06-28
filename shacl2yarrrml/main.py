'''
    @Description:
    
    Script for generating a YARRRML template for a given directory with SHACL RDF files stored in a TTL file that can be used 
    to generate an RDF dataset that complies to the data structure of GA4GH Phenopacket V2.

    @Author: Rosa Zwart
    @Date: 04-06-2024
'''

import shaclutil.loader as loader
import namespace_provider as namespace_provider
import yamlutil.writer as yaml_writer

def get_input_value(input_value, default_value):
    if len(input_value) > 0:
        return input_value
    else:
        return default_value

if __name__ == "__main__":
    default_shacl_folder_name = 'shacl'
    default_single_file_name = None

    shacl_folder_name = input(f'Folder containing SHACL files (default: {default_shacl_folder_name}):')
    shacl_file_name = input(f'Specific SHACL file to load (default: {default_single_file_name}, all SHACL files found in given folder):')

    shacl_g = loader.load_shacl_files(single_file_name=get_input_value(shacl_file_name, default_single_file_name), 
                                            dir_name=get_input_value(shacl_folder_name, default_shacl_folder_name))
    namespace_provider.bind_namespaces(g=shacl_g)
    
    yaml_writer.create_template(input_g=shacl_g)

