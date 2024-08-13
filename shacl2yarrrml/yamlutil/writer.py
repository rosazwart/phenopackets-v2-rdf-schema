import os
import rdflib
from copy import deepcopy

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

import util.common as common_util
import shaclutil.interpreter as shacl_interpreter
import shaclutil.objects as shacl_objects

class Templater:
    def __init__(self, g: rdflib.Graph, prefix_dict: dict, rdf_prefix: str, rdf_namespace: str):
        """
            Creates the YARRRML template. 

            :param g: The RDF graph that stores the SHACL model
            :datatype g: rdflib.Graph

            :param prefix_dict: Dictionary storing the prefixes that are declared in the SHACL files
            :datatype prefix_dict: dict

            :param rdf_prefix: The prefix that is used for defining the RDF entities
            :datatype rdf_prefix: str

            :param rdf_namespace: The namespace that is used for defining the RDF entities
            :datatype rdf_namespace: str
        """
        self.shacl_g = g
        self.prefixes = prefix_dict
        self.rdf_prefix = rdf_prefix
        self.rdf_namespace = rdf_namespace

        self.shacl_interpreter = shacl_interpreter.Interpreter(g=g)

        self.data = CommentedMap()
        self.data['prefixes'] = CommentedMap()
        self.data['mappings'] = CommentedMap()

        self.add_prefixes()
        self.generate_templates_root_nodes()

        self.to_yaml('output/template.yaml')
    
    def add_prefixes(self):
        """
            Add prefixes that are defined in the SHACL files.
        """
        for prefix in self.prefixes:
            namespace = self.prefixes[prefix]
            self.data['prefixes'][prefix] = str(namespace)

    def to_yaml(self, file_path: str):
        """
            Store generated content to a YAML file.

            :param file_path: Path to the location the YAML file will be saved
            :datatype file_path: str
        """
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        curr_wdir = os.getcwd()    
        file_path = os.path.join(curr_wdir, 'shacl2yarrrml', file_path)

        with open(file_path, 'w') as f:
            yaml.dump(self.data, f)

    def get_mapping_name(self, nodeshape_name: str):
        """
            Get the name of the nodeshape for the mapping in YARRRML.

            :param nodeshape_name: Name of the nodeshape
            :datatype nodeshape_name: str

            :returns: The name for the nodeshape of the mapping
            :rtype: str
        """
        return f'{nodeshape_name}Mapping'
    
    def add_source_mapping(self, mapping: CommentedMap, filename: str, path: list):
        """
            Add the source for the given mapping being a JSON file.

            :param mapping: The mapping that will be modified by adding the source parameters
            :datatype mapping: CommentedMap

            :param filename: The name of the JSON file
            :datatype filename: str

            :param path: The hierarchy of the nodeshapes that is used to iterate correctly for the mapping of the current nodeshape
            :datatype path: list
        """
        mapping['sources'] = CommentedSeq()

        sources_info_map = CommentedMap()
        sources_info_map['access'] = filename
        sources_info_map['referenceFormulation'] = 'jsonpath'
        sources_info_map['iterator'] = f'$.{'.'.join(path)}'

        mapping['sources'].append(sources_info_map)

    def add_literaltype_mapping(self, mapping_map: CommentedMap, associated_literaltypes: list):
        """
            Add all associated literal types in the mapping of the nodeshape.

            :param mapping_map: The mapping that will be modified by adding literal types
            :datatype mapping_map: CommentedMap

            :param associated_literaltypes: The literal types associated to this mapping
            :datatype associated_literaltypes: list
        """
        for associated_literaltype in associated_literaltypes:
            value_rel_path = []
            value_rel_path += associated_literaltype.rel_path

            value_name = associated_literaltype.nodekind_name.replace(':', '_')
            value_rel_path.append(value_name)

            if associated_literaltype.literal_type == 'IRI':
                property_map = CommentedSeq()

                property_map.append('a')
                property_map.append(f'$({'.'.join(value_rel_path)})')
                property_map.append('schema:URL')
                property_map.fa.set_flow_style()

                mapping_map['po'].append(property_map)

    def add_literal_mapping(self, mapping_map: CommentedMap, associated_literals: list):
        """
            Add all associated literals in the mapping of the nodeshape.

            :param mapping_map: The mapping that will be modified by adding literal types
            :datatype mapping_map: CommentedMap

            :param associated_literals: The literals associated to this mapping
            :datatype associated_literals: list
        """
        for associated_literal in associated_literals:
            value_rel_path = []
            value_rel_path += associated_literal.rel_path

            value_name = associated_literal.literal_type.replace(':', '_')
            path_name = associated_literal.path_name.replace(':', '_')
            value_rel_path.append(path_name)
            value_rel_path.append(value_name)

            if associated_literal.literal_type == 'sh:IRI':
                property_map = CommentedSeq()

                property_map.append(associated_literal.path_name)

                if associated_literal.max_count == 1:
                    property_map.append(f'$({'.'.join(value_rel_path)})')
                else:
                    property_map.append(f"$({'.'.join(value_rel_path)}[*])")

                property_map.append('schema:URL')
                property_map.fa.set_flow_style()

                mapping_map['po'].append(property_map)

            else: 
                property_map = CommentedMap()

                property_map['p'] = associated_literal.path_name

                property_map['o'] = CommentedMap()

                property_map['o']['value'] = f'$({'.'.join(value_rel_path)})'
                property_map['o']['datatype'] = associated_literal.literal_type

                mapping_map['po'].append(property_map)

    def add_all_literals_mapping(self, mapping_map: CommentedMap, nodeshape: shacl_objects.NodeShapeNode, rel_path: list = []):
        """
            Add all mappings that relate to literals and literal types. 

            :param mapping_map: The mapping that will be modified by adding literal types
            :datatype mapping_map: CommentedMap

            :param nodeshape: The nodeshape that is mapped
            :datatype nodeshape: shacl_objects.NodeShapeNode
        """
        associated_literals, associated_literaltypes = self.shacl_interpreter.get_associated_literals(from_node=nodeshape.node, rel_path=rel_path)

        self.add_literaltype_mapping(mapping_map=mapping_map, associated_literaltypes=associated_literaltypes)
        self.add_literal_mapping(mapping_map=mapping_map, associated_literals=associated_literals)

    def add_type_mapping(self, mapping_map: CommentedMap, nodeshape: shacl_objects.NodeShapeNode):
        """
            Add all mappings that relate to types.

            :param mapping_map: The mapping that will be modified by adding types
            :datatype mapping_map: CommentedMap

            :param nodeshape: The nodeshape that is mapped
            :datatype nodeshape: shacl_objects.NodeShapeNode
        """
        associated_types = self.shacl_interpreter.get_associated_types(from_node=nodeshape.node)

        for associated_type in associated_types:
            type_mapping = CommentedSeq()
            type_mapping.append('a')
            type_mapping.append(associated_type.type_name)
            type_mapping.fa.set_flow_style()

            mapping_map['po'].append(type_mapping)

    def get_shape_mapping_name(self, shape_mapping_name: str, path: list):
        """
            Include to the mapping name the previous hierarchy nodeshapes. TODO: At the moment limited to a depth of 3.

            :param shape_mapping_name: The name of the mapping without considering the hierarchy
            :datatype shape_mapping_name: str

            :param path: The nodeshape hierarchy expressed in list
            :datatype path: list

            :returns: Name of mapping considering the nodeshape hierarchy
            :rtype: str
        """
        if len(path):
            if len(path) == 1:
                shape_mapping_name = f'{path[-1].replace('[*]', '')}{shape_mapping_name}'
            elif len(path) == 2:
                shape_mapping_name = f'{path[-2].replace('[*]', '')}{path[-1].replace('[*]', '')}{shape_mapping_name}'
            else:
                shape_mapping_name = f'{path[-3].replace('[*]', '')}{path[-2].replace('[*]', '')}{path[-1].replace('[*]', '')}{shape_mapping_name}'
        return shape_mapping_name

    def add_path_mapping(self, mapping_map: CommentedMap, associated_nodeshape: shacl_objects.NodeShapeNode):
        """
            Add all mappings that relate to the property paths of the current nodeshape mapping.

            :param mapping_map: The mapping that will be modified by adding path
            :datatype mapping_map: CommentedMap

            :param associated_nodeshape: The nodeshape that is the object/target of the property path
            :datatype associated_nodeshape: shacl_objects.NodeShapeNode
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
            Add all mappings that relate to the property paths of the current nodeshape mapping given the inverse property paths found in the SHACL model.

            :param mapping_map: The mapping that will be modified by adding paths
            :datatype mapping_map: CommentedMap

            :param associated_nodeshape: The nodeshape that is mapped
            :datatype associated_nodeshape: shacl_objects.NodeShapeNode
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
        """
            Add a mapping that represents a nodeshape from the SHACL model. 

            :param root_node_name: The name of the current initial root nodeshape used for referring to the JSON file as source for the nodeshape mapping
            :datatype root_node_name: str

            :param nodeshape: The current nodeshape for which a mapping is generated
            :datatype nodeshape: shacl_objects.NodeShapeNode

            :param path: The nodeshape hierarchy expressed in list
            :datatype path: list
        """
        curr_nodeshape = deepcopy(nodeshape)
        new_path = deepcopy(path)

        _, _, curr_nodeshape_name = self.shacl_interpreter.basic_interpr.extract_values(node=curr_nodeshape.node)
        node_name = common_util.from_nodeshape_name_to_name(curr_nodeshape_name)
        new_path.append(node_name)

        if nodeshape.max_count == -1:
            new_path[-1] = f'{new_path[-1]}[*]'

        curr_filename = f'{root_node_name.lower()}.json'

        inherited_nodeshapes = self.shacl_interpreter.get_inherited_nodeshapes(root_node=curr_nodeshape.node)
        choice_inherited_nodeshapes = []
        for inherited_nodeshape in inherited_nodeshapes:
            if inherited_nodeshape.from_or:
                choice_inherited_nodeshapes.append(inherited_nodeshape)
        
        if len(choice_inherited_nodeshapes):
            for choice_inherited_nodeshape in choice_inherited_nodeshapes:
                mapping_map = CommentedMap()
                _, _, inherited_nodeshape_name = self.shacl_interpreter.basic_interpr.extract_values(node=choice_inherited_nodeshape.node)
                inherited_node_name = common_util.from_nodeshape_name_to_name(inherited_nodeshape_name)

                self.add_source_mapping(mapping=mapping_map, filename=curr_filename, path=new_path)

                inheritance_path = deepcopy(path)
                inheritance_path.append(inherited_node_name)

                mapping_shape_name = self.get_mapping_name(curr_nodeshape_name)
                mapping_shape_name = self.get_shape_mapping_name(mapping_shape_name, path=inheritance_path)

                mapping_map['s'] = f'{self.rdf_prefix}:{node_name}_$(index)'
                mapping_map['po'] = CommentedSeq()

                self.add_type_mapping(mapping_map=mapping_map, nodeshape=choice_inherited_nodeshape)
                
                self.add_all_literals_mapping(mapping_map=mapping_map, nodeshape=choice_inherited_nodeshape, rel_path=inheritance_path)
                self.add_all_literals_mapping(mapping_map=mapping_map, nodeshape=curr_nodeshape)
                
                self.data['mappings'][mapping_shape_name] = mapping_map
        else:
            mapping_map = CommentedMap()
            self.add_source_mapping(mapping=mapping_map, filename=curr_filename, path=new_path)

            mapping_map['s'] = f'{self.rdf_prefix}:{node_name}_$(index)'
            mapping_map['po'] = CommentedSeq()

            self.add_type_mapping(mapping_map=mapping_map, nodeshape=curr_nodeshape)
            self.add_all_literals_mapping(mapping_map=mapping_map, nodeshape=curr_nodeshape)
            self.add_inverse_path_mapping(mapping_map=mapping_map, nodeshape=curr_nodeshape)
            
            mapping_shape_name = self.get_mapping_name(curr_nodeshape_name)
            mapping_shape_name = self.get_shape_mapping_name(mapping_shape_name, path=path)
            
            self.data['mappings'][mapping_shape_name] = mapping_map

            associated_nodeshapes, associated_literals = self.shacl_interpreter.get_associated_nodes(from_node=curr_nodeshape.node, path=new_path)
            associated_nodeshapes += inherited_nodeshapes

            for associated_nodeshape in associated_nodeshapes:
                self.add_path_mapping(mapping_map=mapping_map, associated_nodeshape=associated_nodeshape)
                self.add_nodeshape_mapping(root_node_name=root_node_name, nodeshape=associated_nodeshape, path=new_path)

            self.add_literal_mapping(mapping_map=mapping_map, associated_literals=associated_literals)

    def generate_templates_root_nodes(self):
        """
            Generate the YARRRML template by generating all mappings for each nodeshape from the SHACL model.
        """
        root_nodeshape_nodes = self.shacl_interpreter.get_root_nodeshapes()

        for root_nodeshape_node in root_nodeshape_nodes:
            root_nodeshape = shacl_objects.NodeShapeNode(node=root_nodeshape_node, path=(), min_count=1, max_count=-1)
            _, _, root_node_name = self.shacl_interpreter.basic_interpr.extract_values(root_nodeshape.node)
            self.add_nodeshape_mapping(root_node_name=root_node_name.replace('Shape', ''), nodeshape=root_nodeshape, path=[])

def create_template(input_g: rdflib.Graph, prefix_dict: dict, rdf_prefix: str, rdf_namespace: str):
    """
        Create  and save YARRRML template given the RDF graph representing the SHACL files.

        :param input_g: RDF graph representing the SHACL files
        :datatype input_g: rdflib.Graph

        :param prefix_dict: Dictionary storing the prefixes that are declared in the SHACL files
        :datatype prefix_dict: dict

        :param rdf_prefix: The prefix that is used for defining the RDF entities
        :datatype rdf_prefix: str

        :param rdf_namespace: The namespace that is used for defining the RDF entities
        :datatype rdf_namespace: str
    """
    Templater(g=input_g, prefix_dict=prefix_dict, rdf_prefix=rdf_prefix, rdf_namespace=rdf_namespace)
