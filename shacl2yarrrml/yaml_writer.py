import os
import rdflib

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

import namespace_provider as namespace_provider
import shacl_interpreter as shacl_interpreter

class Template:
    def __init__(self, g: rdflib.Graph):
        self.data = CommentedMap()

        self.data['prefixes'] = CommentedMap()
        self.data['mappings'] = CommentedMap()

        self.shacl_g = g

        self.add_namespaces()
        self.add_nodeshapes()

        self.to_yaml('output_template.yaml')

    def to_yaml(self, file_path):
        yaml = YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        curr_wdir = os.getcwd()    
        file_path = os.path.join(curr_wdir, 'shacl2yarrrml', file_path)

        with open(file_path, 'w') as f:
            yaml.dump(self.data, f)

    def add_namespaces(self):
        for prefix, namespace in self.shacl_g.namespaces():
            if prefix in namespace_provider.used_prefixes:
                self.data['prefixes'][prefix] = str(namespace)

    def get_target_class(self, node_shape: rdflib.URIRef):
        targeted_classes = shacl_interpreter.get_target_class(g=self.shacl_g, node_shape=node_shape)
        if len(targeted_classes):
            target_class_node = targeted_classes[0][2]  # first triple's object
            target_class_prefix, _, target_class_name = self.shacl_g.compute_qname(target_class_node)

            return target_class_prefix, target_class_name
        else:
            raise ValueError(f'Missing target class of shape {node_shape}')
        
    def add_property(self, property_node: rdflib.URIRef, po_map: CommentedSeq):
        property_shape_triples = shacl_interpreter.find_triples(g=self.shacl_g, query_subject=property_node)

        property_map = CommentedMap()
        property_map['p'] = ''
        property_map['o'] = CommentedMap()

        object_class = shacl_interpreter.get_object_class(g=self.shacl_g, triples=property_shape_triples)
        property_dict = shacl_interpreter.get_property_dict(g=self.shacl_g, property_triples=property_shape_triples)

        property_map['p'] = property_dict['path']
        property_map.yaml_add_eol_comment(comment=f'{property_dict['name']}', key='p')

        if object_class is None:
            property_map['o']['value'] = f'$({property_dict['name'].upper()} FIELD)'

            mapping_comment = f'[{property_dict["minCount"]}, {property_dict["maxCount"]}]'

            property_map['o'].yaml_add_eol_comment(comment=mapping_comment, key='value')
            
            if property_dict['datatype']:
                property_map['o']['datatype'] = property_dict['datatype']

        else:
            choice_comment = ''
            if '|' in object_class:
                choice_comment = f'CHOOSE ONE {object_class}'
                property_map['o']['mapping'] = ''
            else:
                property_map['o']['mapping'] = object_class

            property_map['o'].yaml_add_eol_comment(comment=f'{choice_comment} [{property_dict["minCount"]}, {property_dict["maxCount"]}]', key='mapping')

            property_map['o']['condition'] = CommentedMap()
            property_map['o']['condition']['function'] = 'equal'
            property_map['o']['condition']['parameters'] = CommentedSeq()
            property_map['o']['condition']['parameters'].append(f'[str1, $(ID FROM SUBJECT MAPPING), s]')
            property_map['o']['condition']['parameters'].append(f'[str2, $(ID FROM OBJECT MAPPING), o]')
        
        po_map.append(property_map)

    def add_properties(self, node_shape: rdflib.URIRef, po_map: CommentedSeq):
        property_triples = shacl_interpreter.get_properties(g=self.shacl_g, node_shape=node_shape)

        if len(property_triples):
            for property_triple in property_triples:
                s, p, o = property_triple
                self.add_property(property_node=o, po_map=po_map)

        else:
            po_map.append('')   # TODO:
            po_map.yaml_add_eol_comment('Multiple options for sets of predicate-objects', len(po_map) - 1)
    
    def add_nodeshape(self, node_shape: rdflib.URIRef):
        target_class_prefix, target_class_name = self.get_target_class(node_shape=node_shape)

        mapping_map = CommentedMap()

        mapping_map['sources'] = CommentedSeq()

        sources_info_map = CommentedMap()
        sources_info_map['access'] = 'FILENAME.json'
        sources_info_map['referenceFormulation'] = 'jsonpath'
        sources_info_map['iterator'] = '$.ITERATOR[*]'
        
        sources_info_map.yaml_add_eol_comment(comment='path to field representing all entities', key='iterator')
        
        mapping_map['sources'].append(sources_info_map)


        mapping_map['s'] = f'PREFIX:{target_class_name.lower()}_$(IDENTIFIER)'


        mapping_map['po'] = CommentedSeq()

        type_po_map = CommentedMap()
        type_po_map['p'] = 'rdf:type'
        type_po_map['o'] = f'{target_class_prefix}:{target_class_name}'

        mapping_map['po'].append(type_po_map)


        self.add_properties(node_shape=node_shape, po_map=mapping_map['po'])

        self.data['mappings'][target_class_name] = mapping_map

    def add_nodeshapes(self):
        nodeshape_triples = shacl_interpreter.get_all_nodeshapes(self.shacl_g)
        for nodeshape_triple in nodeshape_triples:
            s, p, o = nodeshape_triple
            self.add_nodeshape(node_shape=s)


def create_template(input_g: rdflib.Graph):
    Template(g=input_g)