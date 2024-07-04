import rdflib
from typing import List, Tuple
from copy import deepcopy

import namespace_provider as namespace_provider
import util.common as common_util
import shaclutil.objects as shacl_objects

class BasicInterpreter:
    def __init__(self, g: rdflib.Graph):
        self.shacl_g = g

    def extract_values(self, node: rdflib.URIRef):
        """
            Returns `prefix`, `url`, `name`.
        """
        try:
            return self.shacl_g.namespace_manager.compute_qname(node)
        except ValueError:
            return None, None, None

    def find_triples(self, query_subject = None, query_predicate = None, query_object = None) -> List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]:
        """
            Find triples that comply with given query.
        """
        triples = []
        for subj, predic, obj in self.shacl_g.triples((query_subject, query_predicate, query_object)):
            triples.append((subj, predic, obj))
        return triples

    def find_first_triple(self, query_subject = None, query_predicate = None, query_object = None) -> Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef] | None:
        """
            Find first triple that has been collected complying with given query.
        """
        triples = self.find_triples(query_subject=query_subject, query_predicate=query_predicate, query_object=query_object)
        if len(triples) > 0:
            return triples[0]
        else:
            return None

    def get_class_nodes(self, class_node: rdflib.URIRef) -> List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]:
        """
        """
        return self.find_triples(query_predicate=rdflib.URIRef('http://www.w3.org/ns/shacl#class'), query_object=class_node)

    def get_node_nodes(self, nodeshape_node: rdflib.URIRef) -> List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]:
        """
        """
        return self.find_triples(query_predicate=rdflib.URIRef('http://www.w3.org/ns/shacl#node'), query_object=nodeshape_node)
        
    def get_targetclass_node(self, nodeshape_node: rdflib.URIRef):
        """
        """
        targetclass_triples = self.find_triples(query_subject=nodeshape_node, query_predicate=namespace_provider.SH.targetClass)
        if len(targetclass_triples):
            _, _, node_class = targetclass_triples[0]
            return node_class
        else:
            return None

    def get_property_attr_dict(self, property_attr_triples: list):
        """
        """
        property_attr_dict = {}
        for property_attr_triple in property_attr_triples:
            _, attr_predicate, attr_target = property_attr_triple

            property_attr_dict[attr_predicate] = attr_target
        return property_attr_dict
    
    def get_property_path(self, property_attr_dict: dict):
        """
        """
        if namespace_provider.SH.path in property_attr_dict:
            return property_attr_dict[namespace_provider.SH.path]
        else:
            return None
        
    def get_property_cardinality(self, property_attr_dict: dict):
        """
        """
        if namespace_provider.SH.qualifiedMinCount in property_attr_dict:
            min_count = int(property_attr_dict[namespace_provider.SH.qualifiedMinCount])
        elif namespace_provider.SH.minCount in property_attr_dict:
            min_count = int(property_attr_dict[namespace_provider.SH.minCount])
        else:
            min_count = 0

        if namespace_provider.SH.qualifiedMaxCount in property_attr_dict:
            max_count = int(property_attr_dict[namespace_provider.SH.qualifiedMaxCount])
        elif namespace_provider.SH.maxCount in property_attr_dict:
            max_count = int(property_attr_dict[namespace_provider.SH.maxCount])
        else:
            max_count = -1

        return min_count, max_count
    
    def get_nodeshape_node_from_class_node(self, class_node: rdflib.URIRef):
        """
        """
        targetclass_triple = self.find_first_triple(query_predicate=namespace_provider.SH.targetClass, query_object=class_node)
        if targetclass_triple:
            nodeshape_node, _, _ = targetclass_triple
            return nodeshape_node
        else:
            raise Exception(f'Class node {class_node} lacks a nodeshape it represents.')
        
    def get_nested_nodes(self, root_node: rdflib.URIRef):
        """
        """
        from_root_node_triples = self.find_triples(query_subject=root_node)

        reached_end = False
        first_nodeshape_node = None
        rest_blank_node = None

        for from_root_node_triple in from_root_node_triples:
            _, p, o = from_root_node_triple

            if p == rdflib.URIRef(namespace_provider.RDF.first):
                first_triple = self.find_first_triple(query_subject=o)
                _, class_or_node, class_or_nodeshape_node = first_triple

                if class_or_node == rdflib.URIRef('http://www.w3.org/ns/shacl#class'):
                    first_nodeshape_node = self.get_nodeshape_node_from_class_node(class_or_nodeshape_node)
                else:
                    first_nodeshape_node = class_or_nodeshape_node

            elif p == rdflib.URIRef(namespace_provider.RDF.rest):    
                if o == rdflib.URIRef(namespace_provider.RDF.nil):
                    reached_end = True
                else:
                    rest_blank_node = o

        if reached_end:
            nested_nodes = []
        else:
            nested_nodes = self.get_nested_nodes(root_node=rest_blank_node)

        nested_nodes.append(first_nodeshape_node)
        return nested_nodes
    
    def get_target_nodeshape_nodes_from_or_node(self, or_node: rdflib.URIRef, min_count: int, max_count: int, path: list, property_path_name: str):
        """
        """
        associated_nodeshape_nodes = []

        or_target_nodeshape_nodes = self.get_nested_nodes(root_node=or_node)
        for or_target_nodeshape_node in or_target_nodeshape_nodes:
            associated_nodeshape_nodes.append(shacl_objects.NodeShapeNode(node=or_target_nodeshape_node, property_path=property_path_name, path=path, min_count=min_count, max_count=max_count))

        return associated_nodeshape_nodes

class Interpreter:
    def __init__(self, g: rdflib.Graph):
        self.shacl_g = g
        self.basic_interpr = BasicInterpreter(g=g)

    def comment_or_constraints(self, min_count: int, max_count: int, or_nodeshapes_list: list):
        """
        """
        or_nodeshape_names = []
        for or_nodeshape in or_nodeshapes_list:
            _, _, or_nodeshape_name = self.basic_interpr.extract_values(node=or_nodeshape.node)
            or_nodeshape_names.append(common_util.from_nodeshape_name_to_name(or_nodeshape_name))

        for or_nodeshape in or_nodeshapes_list:
            or_nodeshape.comment = f'Provide with cardinality [{min_count}, {max_count}] from the following: {' OR '.join(or_nodeshape_names)}'

    def comment_constraints(self, nodeshape: shacl_objects.NodeShapeNode):
        """
        """
        if nodeshape.max_count == -1:
            max_count_str = '*'
        else:
            max_count_str = str(nodeshape.max_count)

        nodeshape.comment = f'[{nodeshape.min_count}, {max_count_str}]'

    def get_all_nodeshapes(self) -> List[rdflib.URIRef]:
        """
            Get all nodeshape nodes found in the complete SHACL graph.
        """
        nodeshape_nodes = []
        type_to_nodeshape_triples = self.basic_interpr.find_triples(query_predicate=rdflib.URIRef(namespace_provider.RDF.type),
                                                                    query_object=rdflib.URIRef(namespace_provider.SH.NodeShape))
        for type_to_nodeshape_triple in type_to_nodeshape_triples:
            nodeshape_node, _, _ = type_to_nodeshape_triple
            nodeshape_nodes.append(nodeshape_node)

        return nodeshape_nodes
        
    def is_referred_node_class_or_shape(self, class_node: rdflib.URIRef | None = None, nodeshape_node: rdflib.URIRef | None = None):
        """
        """
        to_class_to_nodeshape_triples = []
        if class_node:
            to_class_to_nodeshape_triples += self.basic_interpr.get_class_nodes(class_node=class_node)
        if nodeshape_node:
            to_class_to_nodeshape_triples += self.basic_interpr.get_node_nodes(nodeshape_node=nodeshape_node)
        
        if len(to_class_to_nodeshape_triples):
            return True
        else:
            return False
        
    def get_property_path_counter_dict(self, prop_triples: list):
        """
        """
        prop_paths_counter_dict = {}

        for prop_triple in prop_triples:
            _, _, prop_node = prop_triple
            prop_attr_triples = self.basic_interpr.find_triples(query_subject=prop_node)
            prop_dict = self.basic_interpr.get_property_attr_dict(prop_attr_triples)
            
            prop_path = self.basic_interpr.get_property_path(prop_dict)
            common_util.add_to_dict_of_counters(dict_values=prop_paths_counter_dict, key=prop_path,
                                                add_number=1)

        return prop_paths_counter_dict

    def get_qualifiedvalue_target_nodeshapes(self, prop_dict: dict, path: list, property_path_name: str):
        """
        """
        nodeshape_node_list = []

        min_count, max_count = self.basic_interpr.get_property_cardinality(prop_dict)

        qualifiedvalue_blank_node = prop_dict[namespace_provider.SH.qualifiedValueShape]
        qualifiedvalue_attributes = self.basic_interpr.find_triples(query_subject=qualifiedvalue_blank_node)
        qualifiedvalue_dict = self.basic_interpr.get_property_attr_dict(qualifiedvalue_attributes)

        target_nodeshape_node = None

        if rdflib.URIRef('http://www.w3.org/ns/shacl#or') in qualifiedvalue_dict:
            or_node = qualifiedvalue_dict[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
            or_nodes = self.basic_interpr.get_target_nodeshape_nodes_from_or_node(or_node=or_node, min_count=min_count, max_count=max_count, path=path, property_path_name=property_path_name)
            nodeshape_node_list += or_nodes
            self.comment_or_constraints(min_count=min_count, max_count=max_count, or_nodeshapes_list=or_nodes)
        else:
            if namespace_provider.SH.node in qualifiedvalue_dict:
                target_nodeshape_node = qualifiedvalue_dict[namespace_provider.SH.node]

            elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in qualifiedvalue_dict:
                target_class_node = qualifiedvalue_dict[rdflib.URIRef('http://www.w3.org/ns/shacl#class')]
                target_nodeshape_node = self.basic_interpr.get_nodeshape_node_from_class_node(target_class_node)

            if target_nodeshape_node:
                nodeshape_obj = shacl_objects.NodeShapeNode(node=target_nodeshape_node, property_path=property_path_name, path=path, min_count=min_count, max_count=max_count)
                self.comment_constraints(nodeshape=nodeshape_obj)
                nodeshape_node_list.append(nodeshape_obj)
        
        return nodeshape_node_list
        
    def get_property_target_nodeshapes(self, property_node: rdflib.URIRef, path_counter_dict: dict, path: list):
        """
        """
        property_attributes = self.basic_interpr.find_triples(query_subject=property_node)
        prop_dict = self.basic_interpr.get_property_attr_dict(property_attributes)

        target_nodeshape_nodes = []

        if namespace_provider.SH.path in prop_dict:
            path_node = prop_dict[namespace_provider.SH.path]
            path_occurrence = path_counter_dict[path_node]

            property_path_prefix, _, property_path_id = self.basic_interpr.extract_values(node=path_node)
            if property_path_prefix:
                property_path_name = f'{property_path_prefix}:{property_path_id}'
            else:
                property_path_name = None

            if path_occurrence == 1 or (path_occurrence > 1 and namespace_provider.SH.qualifiedValueShape in prop_dict):
                
                if path_node != namespace_provider.RDF.type:
                    min_count, max_count = self.basic_interpr.get_property_cardinality(prop_dict)

                    if namespace_provider.SH.qualifiedValueShape in prop_dict:
                        target_nodeshape_nodes += self.get_qualifiedvalue_target_nodeshapes(prop_dict, path, property_path_name)

                    elif namespace_provider.SH.node in prop_dict:
                        target_nodeshape_node = prop_dict[namespace_provider.SH.node]
                        target_nodeshape_obj = shacl_objects.NodeShapeNode(node=target_nodeshape_node, property_path=property_path_name, path=path, min_count=min_count, max_count=max_count)
                        self.comment_constraints(nodeshape=target_nodeshape_obj)
                        target_nodeshape_nodes.append(target_nodeshape_obj)

                    elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in prop_dict:
                        target_class_node = prop_dict[rdflib.URIRef('http://www.w3.org/ns/shacl#class')]
                        target_nodeshape_node = self.basic_interpr.get_nodeshape_node_from_class_node(target_class_node)
                        target_nodeshape_obj = shacl_objects.NodeShapeNode(node=target_nodeshape_node, property_path=property_path_name, path=path, min_count=min_count, max_count=max_count)
                        self.comment_constraints(nodeshape=target_nodeshape_obj)
                        target_nodeshape_nodes.append(target_nodeshape_obj)

        return target_nodeshape_nodes
        
    def get_associated_nodeshapes(self, from_node: rdflib.URIRef, path: list):
        """
        """
        from_node_property_triples = self.basic_interpr.find_triples(query_subject=from_node, query_predicate=namespace_provider.SH.property)
        path_counter_dict = self.get_property_path_counter_dict(prop_triples=from_node_property_triples)

        associated_nodeshapes = []

        for property_triple in from_node_property_triples:
            _, _, property_node = property_triple
            associated_nodeshapes += self.get_property_target_nodeshapes(property_node, path_counter_dict, path)

        return associated_nodeshapes
    
    def get_inverse_associated_nodeshapes(self, from_node: rdflib.URIRef, path: list):
        """
        """
        inverse_associated_nodeshapes = []

        inverse_path_triples = self.basic_interpr.find_triples(query_predicate=rdflib.URIRef(namespace_provider.SH.inversePath))

        for inverse_path_triple in inverse_path_triples:
            blank_path_node, _, inverse_path = inverse_path_triple

            inverse_path_prefix, _, inverse_path_id = self.basic_interpr.extract_values(inverse_path)
            inverse_path_name = f'{inverse_path_prefix}:{inverse_path_id}'

            blank_path_node_triples = self.basic_interpr.find_triples(query_object=blank_path_node)
            for blank_path_node_triple in blank_path_node_triples:
                property_node, _, _ = blank_path_node_triple
                prop_attr_triples = self.basic_interpr.find_triples(query_subject=property_node)
                prop_attributes = self.basic_interpr.get_property_attr_dict(property_attr_triples=prop_attr_triples)

                if rdflib.URIRef(namespace_provider.SH.node) in prop_attributes:
                    target_nodeshape_node = prop_attributes[rdflib.URIRef(namespace_provider.SH.node)]
                
                elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in prop_attributes:
                    target_class_node = prop_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#class')]
                    target_nodeshape_node = self.basic_interpr.get_nodeshape_node_from_class_node(target_class_node)

                else:
                    target_nodeshape_node = None

                if target_nodeshape_node == from_node:
                    min_count, max_count = self.basic_interpr.get_property_cardinality(prop_attributes)

                    nodeshape_triple = self.basic_interpr.find_first_triple(query_object=property_node)
                    if nodeshape_triple:
                        inverse_target_nodeshape_node, _, _ = nodeshape_triple
                        inverse_associated_nodeshapes.append(shacl_objects.NodeShapeNode(node=inverse_target_nodeshape_node, property_path=inverse_path_name,
                                                                                         path=path, min_count=min_count, max_count=max_count))

        return inverse_associated_nodeshapes
    
    def get_inherited_nodeshapes(self, root_node: rdflib.URIRef):
        """
        """
        inherited_nodeshapes = []
        inherited_triples = self.basic_interpr.find_triples(query_subject=root_node, query_predicate=namespace_provider.SH.node)

        for inherited_triple in inherited_triples:
            _, _, inherited_nodeshape_node = inherited_triple
            inherited_nodeshape_obj = shacl_objects.NodeShapeNode(node=inherited_nodeshape_node)
            self.comment_constraints(nodeshape=inherited_nodeshape_obj)
            inherited_nodeshapes.append(inherited_nodeshape_obj)
        
        return inherited_nodeshapes
    
    def get_associated_types(self, from_node: rdflib.URIRef):
        """
        """
        associated_types = []

        from_node_property_triples = self.basic_interpr.find_triples(query_subject=from_node, query_predicate=namespace_provider.SH.property)
        for property_triple in from_node_property_triples:
            _, _, property_node = property_triple
            prop_attr_triples = self.basic_interpr.find_triples(query_subject=property_node)
            prop_attr = self.basic_interpr.get_property_attr_dict(prop_attr_triples)

            path = self.basic_interpr.get_property_path(prop_attr)

            if path == namespace_provider.RDF.type:
                if namespace_provider.SH.hasValue in prop_attr:
                    type_prefix, _, type_name = self.basic_interpr.extract_values(prop_attr[namespace_provider.SH.hasValue])
                    associated_types.append(shacl_objects.TypeNode(type_name=f'{type_prefix}:{type_name}'))
                elif namespace_provider.SH.qualifiedValueShape in prop_attr:
                    qualifiedvalue_node = prop_attr[namespace_provider.SH.qualifiedValueShape]
                    qualifiedvalue_triples = self.basic_interpr.find_triples(query_subject=qualifiedvalue_node)
                    qualifiedvalue_attr = self.basic_interpr.get_property_attr_dict(qualifiedvalue_triples)
                    if namespace_provider.SH.hasValue in qualifiedvalue_attr:
                        type_prefix, _, type_name = self.basic_interpr.extract_values(qualifiedvalue_attr[namespace_provider.SH.hasValue])
                        associated_types.append(shacl_objects.TypeNode(type_name=f'{type_prefix}:{type_name}'))

        from_node_targetclass_triples = self.basic_interpr.find_triples(query_subject=from_node, query_predicate=namespace_provider.SH.targetClass)
        for from_node_targetclass_triple in from_node_targetclass_triples:
            _, _, targetclass_node = from_node_targetclass_triple
            type_prefix, _, type_name = self.basic_interpr.extract_values(targetclass_node)
            associated_types.append(shacl_objects.TypeNode(type_name=f'{type_prefix}:{type_name}'))

        for inherited_nodeshape in self.get_inherited_nodeshapes(from_node):
            associated_types += self.get_associated_types(inherited_nodeshape.node)

        return associated_types
    
    def get_associated_literals(self, from_node: rdflib.URIRef, rel_path: list, include_inherited: bool = True):
        """
        """
        from_node_property_triples = self.basic_interpr.find_triples(query_subject=from_node, query_predicate=namespace_provider.SH.property)
        associated_literals = []

        for property_triple in from_node_property_triples:
            _, _, property_node = property_triple
            prop_attr_triples = self.basic_interpr.find_triples(query_subject=property_node)
            prop_attr = self.basic_interpr.get_property_attr_dict(prop_attr_triples)

            path = self.basic_interpr.get_property_path(prop_attr)
            path_prefix, _, path_name = self.basic_interpr.extract_values(path)
            
            if namespace_provider.SH.datatype in prop_attr:
                literal_datatype_node = prop_attr[namespace_provider.SH.datatype]
                _, _, literal_type = self.basic_interpr.extract_values(literal_datatype_node)

                if namespace_provider.SH.name in prop_attr:
                    literal_name = str(prop_attr[namespace_provider.SH.name])
                else:
                    raise Exception(f'Literal node {path}, {literal_type} does not have a given name')
                
                associated_literals.append(shacl_objects.LiteralNode(path_name=f'{path_prefix}:{path_name}', rel_path=rel_path, literal_name=literal_name, literal_type=literal_type))

            elif path == namespace_provider.RDF.type and namespace_provider.SH.qualifiedValueShape in prop_attr:
                qualifiedvalue_node = prop_attr[namespace_provider.SH.qualifiedValueShape]
                qualifiedvalue_triples = self.basic_interpr.find_triples(query_subject=qualifiedvalue_node)
                qualifiedvalue_attr = self.basic_interpr.get_property_attr_dict(qualifiedvalue_triples)

                if namespace_provider.SH.nodeKind in qualifiedvalue_attr:
                    nodekind_node = qualifiedvalue_attr[namespace_provider.SH.nodeKind]
                    nodekind_prefix, _, nodekind_name = self.basic_interpr.extract_values(nodekind_node)
                    associated_literals.append(shacl_objects.LiteralNode(path_name=f'{path_prefix}:{path_name}', rel_path=rel_path, literal_name=f'{path_prefix}:{path_name}', literal_type=nodekind_name, nodekind_name=f'{nodekind_prefix}:{nodekind_name}'))
        
        if include_inherited:
            for inherited_nodeshape in self.get_inherited_nodeshapes(from_node):
                _, _, inherited_nodeshape_name = self.basic_interpr.extract_values(inherited_nodeshape.node)
                new_path = deepcopy(rel_path)
                new_path.append(common_util.from_nodeshape_name_to_name(inherited_nodeshape_name))
                associated_literals += self.get_associated_literals(inherited_nodeshape.node, rel_path=new_path, include_inherited=include_inherited)

        return associated_literals
    
    def get_root_nodeshapes(self):
        """
        """
        root_nodeshapes = []

        all_nodeshape_nodes = self.get_all_nodeshapes()
        for nodeshape_node in all_nodeshape_nodes:
            class_node = self.basic_interpr.get_targetclass_node(nodeshape_node)

            if not self.is_referred_node_class_or_shape(class_node=class_node, nodeshape_node=nodeshape_node):
                root_nodeshapes.append(nodeshape_node)

        return root_nodeshapes