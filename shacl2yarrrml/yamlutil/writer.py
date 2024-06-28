import os
import rdflib

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

import namespace_provider as namespace_provider
import shaclutil.interpreter as shacl_interpreter
import jsonutil.writer as json_writer

class Templater:
    def __init__(self, g: rdflib.Graph):
        self.shacl_interpreter = shacl_interpreter.Interpreter(g=g)

        self.data = CommentedMap()

        self.data['prefixes'] = CommentedMap()
        self.data['mappings'] = CommentedMap()

        self.shacl_g = g

        self.add_hierarchy()
        self.add_prefixes()
        #self.add_mappings()

        self.to_yaml('output/output_template.yaml')

    def to_yaml(self, file_path):
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        curr_wdir = os.getcwd()    
        file_path = os.path.join(curr_wdir, 'shacl2yarrrml', file_path)

        with open(file_path, 'w') as f:
            yaml.dump(self.data, f)
    
    def add_prefixes(self):
        for prefix, namespace in self.shacl_g.namespaces():
            if prefix in namespace_provider.used_prefixes:
                self.data['prefixes'][prefix] = str(namespace)

    def add_source_mapping(self, mapping: CommentedMap):
        mapping['sources'] = CommentedSeq()

        sources_info_map = CommentedMap()
        sources_info_map['access'] = 'FILENAME.json'
        sources_info_map['referenceFormulation'] = 'jsonpath'
        sources_info_map['iterator'] = '$.ITERATOR[*]'

        sources_info_map.yaml_add_eol_comment(comment='path to field representing all entities', key='iterator')

        mapping['sources'].append(sources_info_map)

    def add_nodeshape(self, nodeshape_node: rdflib.URIRef):
        _, _, nodeshape_name = self.shacl_interpreter.get_node_values(node=nodeshape_node)
        nodeshape_mapping_name = f'{nodeshape_name}Mapping'

        mapping_map = CommentedMap()

        self.add_source_mapping(mapping=mapping_map)

        self.data['mappings'][nodeshape_mapping_name] = mapping_map
        
    def add_mappings(self):
        nodeshape_triples = self.shacl_interpreter.get_all_nodeshapes()
        for nodeshape_triple in nodeshape_triples:
            s, p, o = nodeshape_triple
            self.add_nodeshape(nodeshape_node=s)

    def add_hierarchy(self):
        all_nodeshape_nodes = []
        nodeshape_triples = self.shacl_interpreter.get_all_nodeshapes()
        for nodeshape_triple in nodeshape_triples:
            s, _, _ = nodeshape_triple
            all_nodeshape_nodes.append(s)

        root_nodes = self.shacl_interpreter.find_root_nodeshape(all_nodeshape_nodes=all_nodeshape_nodes)

        for root_node in root_nodes:
            root_dict = self.shacl_interpreter.get_hierarchy(root_node=root_node)

            _, _, nodeshape_name = self.shacl_interpreter.get_node_values(node=root_node)

            json_writer.store_json_file(file_name=f'{nodeshape_name.replace('Shape', '')}.json',
                                        dict_values=root_dict)

def create_template(input_g: rdflib.Graph):
    Templater(g=input_g)