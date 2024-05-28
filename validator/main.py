'''
    @Description:
    
    Script for validating a given RDF dataset stored in a TTL file with the expected data model 
    structure of GA4GH Phenopacket V2 which is represented in TTL files (SHACL RDF) found in a given directory.

    @Author: Rosa Zwart
    @Date: 28-05-2024
'''

import os
from pprint import pprint
from rdflib import Graph
from pyshacl import validate

def print_g(g):
    for stmt in g:
        pprint(stmt)

def get_rdf_graph(rdf_file_name: str = 'phenopacketExample.ttl'):
    curr_wdir = os.getcwd()
    rdf_file_path = os.path.join(curr_wdir, 'example-rdf', rdf_file_name)

    g = Graph()
    g.parse(rdf_file_path)

    print('RDF graph created from file', rdf_file_name)

    return g

def get_shacl_graph(dir_name: str = 'shacl'):
    curr_wdir = os.getcwd()

    g = Graph()

    for file_name in os.listdir(dir_name):
        file_path = os.path.join(curr_wdir, dir_name, file_name)
        if os.path.isfile(file_path):
            print('Add SHACL shapes from', file_name)
            g.parse(file_path)

    print('RDF graph with SHACL shapes created from directory', os.path.join(curr_wdir, dir_name))

    return g

if __name__ == "__main__":
    rdf_g = get_rdf_graph()
    shacl_g = get_shacl_graph()

    r = validate(data_graph=rdf_g,
                 shacl_graph=shacl_g)
    conforms, results_graph, results_text = r

    print('\n', results_text)
    
