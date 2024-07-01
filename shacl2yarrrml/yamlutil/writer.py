import os
import rdflib
from copy import deepcopy

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

import util.common as common_util
import namespace_provider as namespace_provider
import shaclutil.interpreter as shacl_interpreter
import jsonutil.writer as json_writer

class Templater:
    def __init__(self, g: rdflib.Graph):
        self.shacl_interpreter = shacl_interpreter.Interpreter(g=g)
        self.shacl_traverser = shacl_interpreter.Traverser(g=g)

        self.data = CommentedMap()

        self.data['prefixes'] = CommentedMap()
        self.data['mappings'] = CommentedMap()

        self.shacl_g = g

        self.add_prefixes()
        self.template_root_nodes()

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

    def add_source_mapping(self, mapping: CommentedMap, filename: str, path: list):
        mapping['sources'] = CommentedSeq()

        sources_info_map = CommentedMap()
        sources_info_map['access'] = filename
        sources_info_map['referenceFormulation'] = 'jsonpath'
        sources_info_map['iterator'] = f'$.{'.'.join(path)}'

        sources_info_map.yaml_add_eol_comment(comment='path to field representing all entities', key='iterator')

        mapping['sources'].append(sources_info_map)

    def add_root_nodeshape_mapping(self, root_node_name: str, nodeshape_node_obj: shacl_interpreter.AssociatedNodeShapeNode, node_name: str, path: list):
        if nodeshape_node_obj.max_count == -1:
            path[-1] = f'{path[-1]}[*]'

        _, _, nodeshape_name = self.shacl_interpreter.get_node_values(node=nodeshape_node_obj.node)
        nodeshape_mapping_name = f'{nodeshape_name}Mapping'

        mapping_map = CommentedMap()

        self.add_source_mapping(mapping=mapping_map, filename=f'{root_node_name}.json', path=path)

        mapping_map['s'] = f'ex:{node_name}_$(index)'
        mapping_map['po'] = CommentedSeq()

        types = self.shacl_interpreter.get_types_nodeshape(nodeshape_node=nodeshape_node_obj.node)
        for nodeshape_type in types:
            if nodeshape_type:
                type_po_map = CommentedSeq()
                type_po_map.append('a')
                type_po_map.append(nodeshape_type)
                type_po_map.fa.set_flow_style()

                mapping_map['po'].append(type_po_map)

        self.data['mappings'][nodeshape_mapping_name] = mapping_map

        associated_nodeshapes, associated_literals = self.shacl_interpreter.get_associated_shapes(root_node=nodeshape_node_obj.node);

        for associated_nodeshape in associated_nodeshapes:
            _, _, associated_nodeshape_name = self.shacl_interpreter.get_node_values(node=associated_nodeshape.node)
            associated_node_name = common_util.from_nodeshape_name_to_name(associated_nodeshape_name)
            next_path = deepcopy(path)
            next_path.append(associated_node_name)
            self.add_root_nodeshape_mapping(root_node_name=root_node_name, nodeshape_node_obj=associated_nodeshape, node_name=associated_node_name,
                                            path=next_path)

    def template_root_nodes(self):
        all_nodeshape_nodes = self.shacl_interpreter.get_all_nodeshapes()
        root_nodes = self.shacl_interpreter.find_root_nodeshape(all_nodeshape_nodes=all_nodeshape_nodes)

        for root_node in root_nodes:
            print('ROOT NODE:', root_node)
            _, _, root_nodeshape_name = self.shacl_interpreter.get_node_values(node=root_node)
            root_node_name = common_util.from_nodeshape_name_to_name(root_nodeshape_name)

            root_node_obj = shacl_interpreter.AssociatedNodeShapeNode(nodeshape_node=root_node, min_count=1, max_count=-1)

            self.add_root_nodeshape_mapping(root_node_name=root_node_name, nodeshape_node_obj=root_node_obj, node_name=root_node_name,
                                            path=[root_node_name])

def create_template(input_g: rdflib.Graph):
    Templater(g=input_g)