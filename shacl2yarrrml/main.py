'''
    @Description:
    
    Script for generating a YARRRML template for a given directory with SHACL RDF files stored in a TTL file that can be used 
    to generate an RDF dataset that complies to the data structure of GA4GH Phenopacket V2.

    @Author: Rosa Zwart
    @Date: 04-06-2024
'''

import shacl_loader as shacl_loader
import namespace_provider as namespace_provider
import yaml_writer as yaml_writer

if __name__ == "__main__":
    shacl_g = shacl_loader.load_shacl_files()
    namespace_provider.bind_namespaces(g=shacl_g)
    yaml_writer.create_template(input_g=shacl_g)

