import os
import rdflib

def load_shacl_files(dir_name: str = 'shacl'):
    curr_wdir = os.getcwd()

    g = rdflib.Graph()

    for file_name in os.listdir(dir_name):
        file_path = os.path.join(curr_wdir, dir_name, file_name)
        if os.path.isfile(file_path):
            print('Add SHACL shapes from', file_name)
            g.parse(file_path)

    print('RDF graph with SHACL shapes created from directory', os.path.join(curr_wdir, dir_name))

    return g