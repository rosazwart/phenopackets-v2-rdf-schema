'''
    @Description:
    
    Script for validating a given RDF dataset stored in a TTL file with the expected data model 
    structure of GA4GH Phenopacket V2 which is represented in TTL files (SHACL RDF) found in a given directory.

    @Author: Rosa Zwart
    @Date: 05-06-2024
'''

import os
from rdflib import Graph
from pyshacl import validate

def get_rdf_graph(rdf_folder_name: str = 'example-rdf', rdf_file_name: str = 'phenopacketExample.ttl'):
    curr_wdir = os.getcwd()
    rdf_file_path = os.path.join(curr_wdir, rdf_folder_name, rdf_file_name)

    g = Graph()
    g.parse(rdf_file_path)

    print('RDF graph created from', rdf_file_path)

    return g

def get_shacl_graph(dir_name: str = 'shacl'):
    curr_wdir = os.getcwd()

    g = Graph()

    for file_name in os.listdir(dir_name):
        file_path = os.path.join(curr_wdir, dir_name, file_name)
        if os.path.isfile(file_path):
            print('Add SHACL shapes from', file_name)
            g.parse(file_path)

    print('RDF graph with SHACL shapes created from', os.path.join(curr_wdir, dir_name))

    return g

def get_input_value(input_value, default_value):
    if len(input_value) > 0:
        return input_value
    else:
        return default_value

if __name__ == "__main__":
    default_rdf_folder_name = 'example-phenopacket'
    default_rdf_file_name = 'output.ttl'

    default_shacl_folder_name = 'shacl'

    rdf_folder_name = input(f'Folder containing RDF file (default: {default_rdf_folder_name}):')
    rdf_file_name = input(f'Name of RDF file (default: {default_rdf_file_name}):')
    shacl_folder_name = input(f'Folder containing SHACL files (default: {default_shacl_folder_name}):')

    rdf_g = get_rdf_graph(rdf_folder_name=get_input_value(rdf_folder_name, default_rdf_folder_name), 
                          rdf_file_name=get_input_value(rdf_file_name, default_rdf_file_name))
    
    shacl_g = get_shacl_graph(dir_name=get_input_value(shacl_folder_name, default_shacl_folder_name))

    r = validate(data_graph=rdf_g, shacl_graph=shacl_g)
    conforms, results_graph, results_text = r
    print('\n', results_text)
    
