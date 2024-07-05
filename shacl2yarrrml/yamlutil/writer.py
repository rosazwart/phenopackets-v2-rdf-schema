import os
import rdflib
from copy import deepcopy

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

import util.common as common_util
import namespace_provider as namespace_provider
import shaclutil.interpreter as shacl_interpreter
import shaclutil.objects as shacl_objects

class Templater:
    def __init__(self, g: rdflib.Graph):
        self.shacl_g = g

        self.shacl_interpreter = shacl_interpreter.Interpreter(g=g)

        self.data = CommentedMap()
        self.data['prefixes'] = CommentedMap()
        self.data['mappings'] = CommentedMap()

        self.add_prefixes()
        self.generate_templates_root_nodes()

        self.to_yaml('output/template.yaml')
    
    def add_prefixes(self):
        for prefix, namespace in self.shacl_g.namespaces():
            if prefix in namespace_provider.used_prefixes:
                self.data['prefixes'][prefix] = str(namespace)

    def to_yaml(self, file_path):
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        curr_wdir = os.getcwd()    
        file_path = os.path.join(curr_wdir, 'shacl2yarrrml', file_path)

        with open(file_path, 'w') as f:
            yaml.dump(self.data, f)

    def get_mapping_name(self, nodeshape_name: str):
        return f'{nodeshape_name}Mapping'
    
    def add_source_mapping(self, mapping: CommentedMap, filename: str, path: list):
        mapping['sources'] = CommentedSeq()

        sources_info_map = CommentedMap()
        sources_info_map['access'] = filename
        sources_info_map['referenceFormulation'] = 'jsonpath'
        sources_info_map['iterator'] = f'$.{'.'.join(path)}'

        mapping['sources'].append(sources_info_map)

    def add_literal_mapping(self, mapping_map: CommentedMap, nodeshape: shacl_objects.NodeShapeNode):
        """
        """
        associated_literals = self.shacl_interpreter.get_associated_literals(from_node=nodeshape.node, rel_path=[])
        for associated_literal in associated_literals:
            property_map = CommentedMap()

            property_map['p'] = associated_literal.path_name

            property_map['o'] = CommentedMap()

            value_rel_path = []
            value_rel_path += associated_literal.rel_path

            if associated_literal.nodekind_name:
                value_name = associated_literal.nodekind_name.replace(':', '_')
            else:
                value_name = associated_literal.literal_name.replace(':', '_')
            value_rel_path.append(value_name)

            property_map['o']['value'] = f'$({'.'.join(value_rel_path)})'

            if associated_literal.literal_type != 'IRI':
                property_map['o']['datatype'] = associated_literal.literal_type

            mapping_map['po'].append(property_map)

    def add_type_mapping(self, mapping_map: CommentedMap, nodeshape: shacl_objects.NodeShapeNode):
        """
        """
        associated_types = self.shacl_interpreter.get_associated_types(from_node=nodeshape.node)
        for associated_type in associated_types:
            type_mapping = CommentedSeq()
            type_mapping.append('a')
            type_mapping.append(associated_type.type_name)
            type_mapping.fa.set_flow_style()

            mapping_map['po'].append(type_mapping)

    def get_shape_mapping_name(self, shape_mapping_name: str, path: list):
        """"""
        if len(path):
            if len(path) == 1:
                shape_mapping_name = f'{path[-1].replace('[*]', '')}{shape_mapping_name}'
            else:
                shape_mapping_name = f'{path[-2].replace('[*]', '')}{path[-1].replace('[*]', '')}{shape_mapping_name}'
        return shape_mapping_name

    def add_path_mapping(self, mapping_map: CommentedMap, associated_nodeshape: shacl_objects.NodeShapeNode):
        """
        """
        if associated_nodeshape.property_path:
            path_map = CommentedMap()

            path_map['p'] = associated_nodeshape.property_path

            path_map['o'] = CommentedMap()

            _, _, shape_mapping_name = self.shacl_interpreter.basic_interpr.extract_values(associated_nodeshape.node)
            shape_mapping_name = self.get_shape_mapping_name(shape_mapping_name, path=associated_nodeshape.path)

            path_map['o']['mapping'] = f'{shape_mapping_name}Mapping'

            path_map['o']['condition'] = CommentedMap()
            path_map['o']['condition']['function'] = 'equal'
            path_map['o']['condition']['parameters'] = CommentedSeq()

            triples_values = [('str1', '$(index)', 's'), ('str2', '$(parent_index)', 'o')]
            for triple_values in triples_values:
                str_map = CommentedSeq()

                for value in triple_values:
                    str_map.append(value)
                str_map.fa.set_flow_style()

                path_map['o']['condition']['parameters'].append(str_map)

            mapping_map['po'].append(path_map)
    
    def add_inverse_path_mapping(self, mapping_map: CommentedMap, nodeshape: shacl_objects.NodeShapeNode):
        """
        """     
        inverse_associated_nodeshapes = self.shacl_interpreter.get_inverse_associated_nodeshapes(from_node=nodeshape.node, path=nodeshape.path[:-1])
        for inverse_associated_nodeshape in inverse_associated_nodeshapes:
            if inverse_associated_nodeshape.property_path:
                path_map = CommentedMap()

                path_map['p'] = inverse_associated_nodeshape.property_path

                path_map['o'] = CommentedMap()
                _, _, shape_mapping_name = self.shacl_interpreter.basic_interpr.extract_values(inverse_associated_nodeshape.node)
                shape_mapping_name = self.get_shape_mapping_name(shape_mapping_name, path=inverse_associated_nodeshape.path)

                path_map['o']['mapping'] = f'{shape_mapping_name}Mapping'

                path_map['o']['condition'] = CommentedMap()
                path_map['o']['condition']['function'] = 'equal'
                path_map['o']['condition']['parameters'] = CommentedSeq()

                triples_values = [('str1', '$(parent_index)', 's'), ('str2', '$(index)', 'o')]
                for triple_values in triples_values:
                    str_map = CommentedSeq()

                    for value in triple_values:
                        str_map.append(value)
                    str_map.fa.set_flow_style()

                    path_map['o']['condition']['parameters'].append(str_map)

                mapping_map['po'].append(path_map)

    def add_nodeshape_mapping(self, root_node_name: str, nodeshape: shacl_objects.NodeShapeNode, path: list):
        curr_nodeshape = deepcopy(nodeshape)
        new_path = deepcopy(path)

        _, _, curr_nodeshape_name = self.shacl_interpreter.basic_interpr.extract_values(node=curr_nodeshape.node)
        node_name = common_util.from_nodeshape_name_to_name(curr_nodeshape_name)
        new_path.append(node_name)

        if nodeshape.max_count == -1:
            new_path[-1] = f'{new_path[-1]}[*]'

        mapping_map = CommentedMap()

        self.add_source_mapping(mapping=mapping_map, filename=f'{root_node_name}.json', path=new_path)

        mapping_map['s'] = f'ex:{node_name}_$(index)'
        mapping_map['po'] = CommentedSeq()

        self.add_type_mapping(mapping_map=mapping_map, nodeshape=curr_nodeshape)
        self.add_literal_mapping(mapping_map=mapping_map, nodeshape=curr_nodeshape)
        self.add_inverse_path_mapping(mapping_map=mapping_map, nodeshape=curr_nodeshape)
    	
        mapping_shape_name = self.get_mapping_name(curr_nodeshape_name)
        mapping_shape_name = self.get_shape_mapping_name(mapping_shape_name, path=path)
        
        self.data['mappings'][mapping_shape_name] = mapping_map

        associated_nodeshapes = self.shacl_interpreter.get_associated_nodeshapes(from_node=curr_nodeshape.node, path=new_path)

        for associated_nodeshape in associated_nodeshapes:
            self.add_path_mapping(mapping_map=mapping_map, associated_nodeshape=associated_nodeshape)
            self.add_nodeshape_mapping(root_node_name=root_node_name, nodeshape=associated_nodeshape, path=new_path)

    def generate_templates_root_nodes(self):
        root_nodeshape_nodes = self.shacl_interpreter.get_root_nodeshapes()

        for root_nodeshape_node in root_nodeshape_nodes:
            root_nodeshape = shacl_objects.NodeShapeNode(node=root_nodeshape_node, path=(), min_count=1, max_count=-1)
            _, _, root_node_name = self.shacl_interpreter.basic_interpr.extract_values(root_nodeshape.node)
            self.add_nodeshape_mapping(root_node_name=root_node_name.replace('Shape', ''), nodeshape=root_nodeshape, path=[])

def create_template(input_g: rdflib.Graph):
    Templater(g=input_g)
