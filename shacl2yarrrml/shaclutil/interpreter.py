import rdflib
from copy import deepcopy

import namespace_provider as namespace_provider
import util.common as common_util

def get_cardinality(mincount_triple: tuple, maxcount_triple: tuple):
    if mincount_triple:
        _, _, mincount_node = mincount_triple
        mincount = int(mincount_node)
    else:
        mincount = 0

    if maxcount_triple:
        _, _, maxcount_node = maxcount_triple
        maxcount = int(maxcount_node)
    else:
        maxcount = -1

    return mincount, maxcount

class AssociatedLiteral:
    def __init__(self, name: str, literal_type: str, min_count: int, max_count: int):
        self.name = name
        self.type = literal_type
        self.min_count = min_count
        self.max_count = max_count

class AssociatedNodeShapeNode:
    def __init__(self, nodeshape_node: rdflib.URIRef, min_count: int, max_count: int, comment: str = ''):
        self.node = nodeshape_node
        self.min_count = min_count
        self.max_count = max_count
        self.comment = comment

class AssociatedProperty:
    def __init__(self, path: str, path_name: str, target_nodeshape: str, target_nodeshape_node: rdflib.URIRef, inverse: bool = False):
        self.path = path
        self.path_name = path_name
        self.target_nodeshape = target_nodeshape
        self.target_nodeshape_node = target_nodeshape_node
        self.inverse = inverse

class AssociatedPropertyLiteral:
    def __init__(self, path: str, path_name: str, literal_type: rdflib.URIRef | None, relative_path: list = []):
        self.path = path
        self.path_name = path_name
        self.literal_type = literal_type
        self.relative_path = relative_path

class Interpreter:
    def __init__(self, g: rdflib.Graph):
        self.shacl_g = g

    def get_node_values(self, node: rdflib.URIRef):
        """
            Returns `prefix`, `url`, `name`.
        """
        return self.shacl_g.namespace_manager.compute_qname(node)

    def find_triples(self, query_subject = None, query_predicate = None, query_object = None):
        triple_list = []

        for s, p, o in self.shacl_g.triples((query_subject, query_predicate, query_object)):
            triple_list.append((s, p, o))

        return triple_list
    
    def find_first_triple(self, query_subject = None, query_predicate = None, query_object = None):
        triple_list = self.find_triples(query_subject=query_subject, query_predicate=query_predicate, query_object=query_object)

        if len(triple_list) > 0:
            return triple_list[0]
        else:
            return None
        
    def get_class_nodes(self, class_node: rdflib.URIRef):
        return self.find_triples(query_predicate=rdflib.URIRef('http://www.w3.org/ns/shacl#class'),
                                 query_object=class_node)

    def get_node_nodes(self, nodeshape_node: rdflib.URIRef):
        return self.find_triples(query_predicate=rdflib.URIRef('http://www.w3.org/ns/shacl#node'),
                                 query_object=nodeshape_node)

    def get_all_nodeshapes(self):
        """
            Get all nodeshape nodes found in the SHACL graph.
        """
        all_nodeshape_nodes = []
        nodeshape_triples = self.find_triples(query_predicate=rdflib.URIRef(namespace_provider.RDF.type), 
                                              query_object=rdflib.URIRef(namespace_provider.SH.NodeShape))
        for nodeshape_triple in nodeshape_triples:
            s, _, _ = nodeshape_triple
            all_nodeshape_nodes.append(s)

        return all_nodeshape_nodes
        
    def from_class_to_nodeshape(self, class_node: rdflib.URIRef):
        class_node_triple = self.find_first_triple(query_predicate=namespace_provider.SH.targetClass, query_object=class_node)
        if class_node_triple:
            nodeshape_node, _, _ = class_node_triple
            return nodeshape_node
        else:
            return None
        
    def get_nodeshape_node(self, to_class_or_nodeshape_triple: tuple):
        _, class_or_shape, class_or_shape_node = to_class_or_nodeshape_triple

        if class_or_shape == rdflib.URIRef('http://www.w3.org/ns/shacl#class'):
            nodeshape_node = self.from_class_to_nodeshape(class_node=class_or_shape_node)
        else:
            nodeshape_node = class_or_shape_node

        return nodeshape_node
    
    def is_referred_to(self, class_node: rdflib.URIRef | None = None, nodeshape_node: rdflib.URIRef | None = None):
        to_class_or_nodeshape_triples = []
        if class_node:
            to_class_or_nodeshape_triples += self.get_class_nodes(class_node=class_node)
        if nodeshape_node:
            to_class_or_nodeshape_triples += self.get_node_nodes(nodeshape_node=nodeshape_node)

        if len(to_class_or_nodeshape_triples):
            return True
        else:
            return False
        
    def get_targetclass_node(self, nodeshape_node: rdflib.URIRef):
        targetclass_triples = self.find_triples(query_subject=nodeshape_node,
                                                query_predicate=namespace_provider.SH.targetClass)

        if len(targetclass_triples):
            _, _, o = targetclass_triples[0]
            return o
        else:
            return None
        
    def get_nested_nodes(self, root_node: rdflib.URIRef):
        from_root_triples = self.find_triples(query_subject=root_node)

        reached_end = False
        first_nodeshape_node = None
        rest_node = None

        for from_root_triple in from_root_triples:
            _, p, o = from_root_triple

            if p == rdflib.URIRef(namespace_provider.RDF.first):
                first_triple = self.find_first_triple(query_subject=o)
                first_nodeshape_node = self.get_nodeshape_node(to_class_or_nodeshape_triple=first_triple)

            elif p == rdflib.URIRef(namespace_provider.RDF.rest):
                if o == rdflib.URIRef(namespace_provider.RDF.nil):
                    reached_end = True
                else:
                    rest_node = o

        if reached_end:
            nested_nodes = []
        else:
            nested_nodes = self.get_nested_nodes(root_node=rest_node)

        nested_nodes.append(first_nodeshape_node)
        return nested_nodes

    def find_or_node(self, triple: tuple):
        s, _, _ = triple

        parent_triples = self.find_triples(query_object=s)
        for parent_triple in parent_triples:
            _, parent_p, parent_o = parent_triple

            if parent_p == rdflib.URIRef('http://www.w3.org/ns/shacl#or'):
                return parent_o
            
            if parent_p == namespace_provider.SH.property:
                return None
        
        return self.find_or_node(triple=parent_triples[0])
        
    def find_root_nodeshape(self, all_nodeshape_nodes: list):
        root_nodes = []

        for nodeshape_node in all_nodeshape_nodes:
            targetclass_node = self.get_targetclass_node(nodeshape_node=nodeshape_node)

            if not self.is_referred_to(class_node=targetclass_node, nodeshape_node=nodeshape_node):
                root_nodes.append(nodeshape_node)

        return root_nodes
        
    def get_property_dict(self, property_attr_triples: list):
        property_attributes = {}
        for property_attr_triple in property_attr_triples:
            _, p, o = property_attr_triple

            property_attributes[p] = o
        return property_attributes
    
    def get_or_nodeshape_nodes(self, or_root_node: rdflib.URIRef, min_count: int, max_count: int):    
        or_associated_nodeshape_nodes = []

        or_nodeshape_nodes = self.get_nested_nodes(root_node=or_root_node)

        for or_nodeshape_node in or_nodeshape_nodes:
            or_associated_nodeshape_nodes.append(AssociatedNodeShapeNode(nodeshape_node=or_nodeshape_node, min_count=min_count, max_count=max_count))

        return or_associated_nodeshape_nodes
    
    def address_or_constraints(self, min_count: int, max_count: int, or_nodeshapes_list: list):
        or_node_names = []
        for or_nodeshape in or_nodeshapes_list:
            _, _, or_nodeshape_name = self.get_node_values(or_nodeshape.node)
            or_node_names.append(common_util.from_nodeshape_name_to_name(or_nodeshape_name))
    
        for or_nodeshape in or_nodeshapes_list:
            or_nodeshape.comment = f'Provide with cardinality [{min_count}, {max_count}] from the following: {' OR '.join(or_node_names)}'

    def address_constraints(self, min_count: int, max_count: int, nodeshape_node_obj: AssociatedNodeShapeNode):
        if max_count == -1:
            max_count_str = '*'
        else:
            max_count_str = str(max_count)

        nodeshape_node_obj.comment = f'[{min_count}, {max_count_str}]'

    def get_qualified_nodeshapes(self, qualifiedvalue_shape_node: rdflib.URIRef, property_node: rdflib.URIRef):
        nodeshapes_list = []

        qualifiedmincount_triple = self.find_first_triple(query_subject=property_node,
                                                          query_predicate=namespace_provider.SH.qualifiedMinCount)
        qualifiedmaxcount_triple = self.find_first_triple(query_subject=property_node,
                                                          query_predicate=namespace_provider.SH.qualifiedMaxCount)

        min_count, max_count = get_cardinality(mincount_triple=qualifiedmincount_triple, maxcount_triple=qualifiedmaxcount_triple)

        qualifiedvalue_triples = self.find_triples(query_subject=qualifiedvalue_shape_node)
        qualifiedvalue_attributes = self.get_property_dict(qualifiedvalue_triples)

        if namespace_provider.SH.node in qualifiedvalue_attributes:
            nodeshape_node = qualifiedvalue_attributes[namespace_provider.SH.node]
            nodeshape_node_obj = AssociatedNodeShapeNode(nodeshape_node=nodeshape_node, min_count=min_count, max_count=max_count)
            self.address_constraints(min_count=min_count, max_count=max_count, nodeshape_node_obj=nodeshape_node_obj)

            nodeshapes_list.append(nodeshape_node_obj)

        elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in qualifiedvalue_attributes:
            class_node = qualifiedvalue_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#class')]
            nodeshape_node = self.from_class_to_nodeshape(class_node=class_node)

            if nodeshape_node:
                nodeshape_node_obj = AssociatedNodeShapeNode(nodeshape_node=nodeshape_node, min_count=min_count, max_count=max_count)
                self.address_constraints(min_count=min_count, max_count=max_count, nodeshape_node_obj=nodeshape_node_obj)
                nodeshapes_list.append(nodeshape_node_obj)

        elif rdflib.URIRef('http://www.w3.org/ns/shacl#or') in qualifiedvalue_attributes:
            or_root_node = qualifiedvalue_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
            or_nodeshapes_list = self.get_or_nodeshape_nodes(or_root_node=or_root_node, min_count=min_count, max_count=max_count)

            if max_count == 1:
                self.address_or_constraints(min_count=min_count, max_count=max_count, or_nodeshapes_list=or_nodeshapes_list)

            nodeshapes_list += or_nodeshapes_list

        return nodeshapes_list
    
    def get_first_layer_cardinality(self, property_attributes):
        if namespace_provider.SH.minCount in property_attributes:
            min_count = int(property_attributes[namespace_provider.SH.minCount])
        else:
            min_count = 0
        
        if namespace_provider.SH.maxCount in property_attributes:
            max_count = int(property_attributes[namespace_provider.SH.maxCount])
        else:
            max_count = -1

        return min_count, max_count
    
    def get_first_layer_class(self, property_attributes):
        class_node = property_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#class')]
        
        nodeshape_node = self.from_class_to_nodeshape(class_node=class_node)    

        return nodeshape_node
    
    def get_first_layer_nodeshape(self, property_attributes):
        nodeshape_node = property_attributes[namespace_provider.SH.node]
        return nodeshape_node
    
    def get_literal_node(self, property_attributes):
        literal_name = str(property_attributes[namespace_provider.SH.name])
        _, _, literal_type = self.get_node_values(property_attributes[namespace_provider.SH.datatype])

        return AssociatedLiteral(name=literal_name,
                                 literal_type=literal_type,
                                 min_count=1, max_count=1)
    
    def get_variable_type(self, property_attributes: dict):
        literals = []

        type_name_node = property_attributes[namespace_provider.SH.path]
        prefix, _, type_name = self.get_node_values(node=type_name_node)

        if namespace_provider.SH.hasValue not in property_attributes:
            if namespace_provider.SH.qualifiedValueShape in property_attributes:
                qualifiedvalue_shape_node = property_attributes[namespace_provider.SH.qualifiedValueShape]
                qualifiedvalue_triples = self.find_triples(query_subject=qualifiedvalue_shape_node)
                property_attributes = self.get_property_dict(qualifiedvalue_triples)
            
            if namespace_provider.SH.nodeKind in property_attributes and namespace_provider.SH.hasValue not in property_attributes:
                nodekind_node = property_attributes[namespace_provider.SH.nodeKind]
                _, _, nodekind_name = self.get_node_values(node=nodekind_node)
                literals.append(AssociatedLiteral(name=f'{prefix}:{type_name}', literal_type=nodekind_name, min_count=1, max_count=1))
        
        return literals
    
    def get_property_targets(self, property_node: rdflib.URIRef):
        property_attr_triples = self.find_triples(query_subject=property_node)
        property_attributes = self.get_property_dict(property_attr_triples=property_attr_triples)

        nodeshape_nodes = []
        literals = []

        min_count, max_count = self.get_first_layer_cardinality(property_attributes=property_attributes)

        if namespace_provider.SH.path in property_attributes:
            if property_attributes[namespace_provider.SH.path] != namespace_provider.RDF.type:
                if namespace_provider.SH.node in property_attributes:
                    nodeshape_node = self.get_first_layer_nodeshape(property_attributes=property_attributes)
                    nodeshape_node_obj = AssociatedNodeShapeNode(nodeshape_node=nodeshape_node, min_count=min_count, max_count=max_count)
                    self.address_constraints(min_count=min_count, max_count=max_count, nodeshape_node_obj=nodeshape_node_obj)
                    nodeshape_nodes.append(nodeshape_node_obj)

                elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in property_attributes:
                    nodeshape_node = self.get_first_layer_class(property_attributes=property_attributes)
                    nodeshape_node_obj = AssociatedNodeShapeNode(nodeshape_node=nodeshape_node, min_count=min_count, max_count=max_count)
                    self.address_constraints(min_count=min_count, max_count=max_count, nodeshape_node_obj=nodeshape_node_obj)
                    nodeshape_nodes.append(nodeshape_node_obj)
                    
                elif namespace_provider.SH.qualifiedValueShape in property_attributes:
                    nodeshape_nodes += self.get_qualified_nodeshapes(qualifiedvalue_shape_node=property_attributes[namespace_provider.SH.qualifiedValueShape],
                                                                     property_node=property_node)
                    
                elif namespace_provider.SH.datatype in property_attributes:
                    literals.append(self.get_literal_node(property_attributes=property_attributes))

                elif rdflib.URIRef('http://www.w3.org/ns/shacl#or') in property_attributes:
                    or_root_node = property_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
                    or_nodeshapes_list = self.get_or_nodeshape_nodes(or_root_node=or_root_node, min_count=min_count, max_count=max_count)

                    if max_count == 1:
                        self.address_or_constraints(min_count=min_count, max_count=max_count, or_nodeshapes_list=or_nodeshapes_list)

                    nodeshape_nodes += or_nodeshapes_list
            
            else:
                variable_type_literals = self.get_variable_type(property_attributes=property_attributes)
                literals += variable_type_literals
    	
        return nodeshape_nodes, literals

    def get_associated_shapes(self, root_node: rdflib.URIRef):
        property_triples = self.find_triples(query_subject=root_node,
                                             query_predicate=namespace_provider.SH.property)

        associated_nodeshapes = []
        associated_literals = []
        for property_triple in property_triples:
            _, _, property_node = property_triple
            nodeshape_nodes, literals = self.get_property_targets(property_node=property_node)
            associated_nodeshapes += nodeshape_nodes
            associated_literals += literals

        return associated_nodeshapes, associated_literals
    
    def get_path_name(self, path):
        path_triples = self.find_triples(query_object=path)
        for path_triple in path_triples:
            property_node, _, _ = path_triple
            property_triples = self.find_triples(query_subject=property_node)
            property_attributes = self.get_property_dict(property_attr_triples=property_triples)

            if rdflib.term.URIRef(namespace_provider.SH.name) in property_attributes:
                return property_attributes[rdflib.term.URIRef(namespace_provider.SH.name)]

        return ''
        
    def get_associated_literal(self, path: rdflib.URIRef, literal_type: rdflib.URIRef):
        path_prefix, _, path_name = self.get_node_values(path)
        type_prefix, _, type_name = self.get_node_values(literal_type)
        
        return AssociatedPropertyLiteral(path=f'{path_prefix}:{path_name}', path_name=self.get_path_name(path=path),
                                         literal_type=f'{type_prefix}:{type_name}')

    def get_associated_property(self, target_nodeshape_node: rdflib.URIRef, path: rdflib.URIRef, inverse: bool =False):
        path_prefix, _, path_name = self.get_node_values(path)

        if target_nodeshape_node:
            _, _, target_nodeshape_name = self.get_node_values(target_nodeshape_node)

            property_obj = AssociatedProperty(path=f'{path_prefix}:{path_name}', path_name=self.get_path_name(path=path), 
                                              target_nodeshape=target_nodeshape_name,
                                              target_nodeshape_node=target_nodeshape_node, inverse=inverse)
            return property_obj
        
        else:
            return None
        
    def get_direct_target_path(self, property_triples, path):
        property_objs = []
        literal_objs = []

        for property_triple in property_triples: 
            _, _, property_node = property_triple
            property_attr_triples = self.find_triples(query_subject=property_node)
            property_attributes = self.get_property_dict(property_attr_triples=property_attr_triples)

            if property_attributes[rdflib.URIRef(namespace_provider.SH.path)] == path:
                target_nodeshape_node = None

                if rdflib.URIRef('http://www.w3.org/ns/shacl#or') in property_attributes:
                    or_root_node = property_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
                    or_nodeshape_nodes = self.get_nested_nodes(root_node=or_root_node)

                    for or_nodeshape_node in or_nodeshape_nodes:
                        associated_property_obj = self.get_associated_property(target_nodeshape_node=or_nodeshape_node, path=path)
                        if associated_property_obj:
                            property_objs.append(associated_property_obj)
                else:
                    if rdflib.URIRef(namespace_provider.SH.node) in property_attributes:    # paths with sh:node as target
                        target_nodeshape_node = self.get_first_layer_nodeshape(property_attributes=property_attributes)

                    elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in property_attributes:
                        target_nodeshape_node = self.get_first_layer_class(property_attributes=property_attributes)

                    elif rdflib.URIRef(namespace_provider.SH.datatype) in property_attributes:
                        datatype_node = property_attributes[rdflib.URIRef(namespace_provider.SH.datatype)]
                        associated_literal_obj = self.get_associated_literal(path=path, literal_type=datatype_node)
                        if associated_literal_obj:
                            literal_objs.append(associated_literal_obj)

                    associated_property_obj = self.get_associated_property(target_nodeshape_node=target_nodeshape_node, path=path)
                    if associated_property_obj:
                        property_objs.append(associated_property_obj)
                
        return property_objs, literal_objs  
    
    def get_qualified_target_paths(self, property_triples, path):
        property_objs = []

        for property_triple in property_triples: 
            _, _, property_node = property_triple
            property_attr_triples = self.find_triples(query_subject=property_node)
            property_attributes = self.get_property_dict(property_attr_triples=property_attr_triples)

            if property_attributes[rdflib.URIRef(namespace_provider.SH.path)] == path and rdflib.URIRef(namespace_provider.SH.qualifiedValueShape) in property_attributes:
                target_nodeshape_node = None
                
                qualifiedvalue_triples = self.find_triples(query_subject=property_attributes[rdflib.URIRef(namespace_provider.SH.qualifiedValueShape)])
                qualifiedvalue_attributes = self.get_property_dict(qualifiedvalue_triples)

                if rdflib.URIRef('http://www.w3.org/ns/shacl#or') in qualifiedvalue_attributes:
                    or_root_node = qualifiedvalue_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
                    or_nodeshape_nodes = self.get_nested_nodes(root_node=or_root_node)

                    for or_nodeshape_node in or_nodeshape_nodes:
                        associated_property_obj = self.get_associated_property(target_nodeshape_node=or_nodeshape_node, path=path)
                        if associated_property_obj:
                            property_objs.append(associated_property_obj)
                else:
                    if rdflib.URIRef(namespace_provider.SH.node) in qualifiedvalue_attributes:    # paths with sh:node as target
                        target_nodeshape_node = self.get_first_layer_nodeshape(property_attributes=qualifiedvalue_attributes)
                    
                    elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in qualifiedvalue_attributes:
                        target_nodeshape_node = self.get_first_layer_class(property_attributes=qualifiedvalue_attributes)

                associated_property_obj = self.get_associated_property(target_nodeshape_node=target_nodeshape_node, path=path)
                if associated_property_obj:
                    property_objs.append(associated_property_obj)

        return property_objs
    
    def get_inverse_paths(self, root_node: rdflib.URIRef):
        property_objs = []

        inverse_path_triples = self.find_triples(query_predicate=rdflib.URIRef(namespace_provider.SH.inversePath))
        for inverse_path_triple in inverse_path_triples:
            blank_path_node, _, inverse_path = inverse_path_triple

            blank_path_triples = self.find_triples(query_object=blank_path_node)
            for blank_path_triple in blank_path_triples:
                property_node, _, _ = blank_path_triple
                property_attr_triples = self.find_triples(query_subject=property_node)
                property_attributes = self.get_property_dict(property_attr_triples=property_attr_triples)

                if rdflib.URIRef(namespace_provider.SH.node) in property_attributes:    # paths with sh:node as target
                    target_nodeshape_node = self.get_first_layer_nodeshape(property_attributes=property_attributes)

                elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in property_attributes:
                    target_nodeshape_node = self.get_first_layer_class(property_attributes=property_attributes)

                else:
                    target_nodeshape_node = None
                
                if target_nodeshape_node == root_node:
                    nodeshape_triple = self.find_first_triple(query_object=property_node)
                    if nodeshape_triple:
                        target_nodeshape_node, _, _ = nodeshape_triple

                        associated_property_obj = self.get_associated_property(target_nodeshape_node=target_nodeshape_node, path=inverse_path, inverse=True)
                        if associated_property_obj:
                            property_objs.append(associated_property_obj)

        return property_objs
    
    def get_inherited_paths(self, root_node: rdflib.URIRef):
        property_paths = []
        literal_paths = []

        inherited_nodeshapes = self.get_inherited_nodeshape(root_node=root_node)

        for inherited_nodeshape in inherited_nodeshapes:
            inherited_nodeshape_node = inherited_nodeshape.node
            _, _, inherited_nodeshape_name = self.get_node_values(node=inherited_nodeshape_node)

            inherited_property_paths, inherited_literal_paths = self.get_paths(root_node=inherited_nodeshape_node)

            for inherited_literal_path in inherited_literal_paths:
                inherited_literal_path.relative_path = [common_util.from_nodeshape_name_to_name(inherited_nodeshape_name)]   # TODO: only works with inheritance of first order

            property_paths += inherited_property_paths
            literal_paths += inherited_literal_paths

        return property_paths, literal_paths

    def get_paths(self, root_node: rdflib.URIRef):
        property_paths = []
        literal_paths = []

        property_triples = self.find_triples(query_subject=root_node,
                                             query_predicate=namespace_provider.SH.property)
        
        paths_dict = {}

        for property_triple in property_triples: 
            _, _, property_node = property_triple
            property_attr_triples = self.find_triples(query_subject=property_node)
            property_attributes = self.get_property_dict(property_attr_triples=property_attr_triples)

            if rdflib.URIRef(namespace_provider.SH.path) in property_attributes:
                path = property_attributes[rdflib.URIRef(namespace_provider.SH.path)]
                if path == rdflib.URIRef(namespace_provider.RDF.type) and rdflib.URIRef(namespace_provider.SH.qualifiedValueShape) in property_attributes:
                    qualifiedvalue_node = property_attributes[rdflib.URIRef(namespace_provider.SH.qualifiedValueShape)]
                    qualified_attr_triples = self.find_triples(query_subject=qualifiedvalue_node)
                    
                    for qualified_attr_triple in qualified_attr_triples:
                        _, p, o = qualified_attr_triple
                        if p == rdflib.URIRef(namespace_provider.SH.nodeKind):
                            path_prefix, _, path_name = self.get_node_values(path)
                            value_prefix, _, value_name = self.get_node_values(o)

                            literal_obj = AssociatedPropertyLiteral(path=f'{path_prefix}:{path_name}', path_name=f'{value_prefix}:{value_name}', literal_type=None)
                            literal_paths.append(literal_obj)

        for property_triple in property_triples: 
            _, _, property_node = property_triple
            property_attr_triples = self.find_triples(query_subject=property_node)
            property_attributes = self.get_property_dict(property_attr_triples=property_attr_triples)

            if rdflib.URIRef(namespace_provider.SH.path) in property_attributes:
                path = property_attributes[rdflib.URIRef(namespace_provider.SH.path)]

                if path != rdflib.URIRef(namespace_provider.RDF.type):
                    if rdflib.URIRef(namespace_provider.SH.qualifiedValueShape) in property_attributes:
                        common_util.add_to_dict_of_counters(dict_values=paths_dict, 
                                                            key=path, add_number=1)
                    else:
                        common_util.add_to_dict_of_counters(dict_values=paths_dict, 
                                                            key=path, add_number=0)
                    
        for path in paths_dict:
            if not self.find_triples(query_subject=path):  # TODO: inverse paths excluded
                qualifiedvalue_shape_counter = paths_dict[path]

                if qualifiedvalue_shape_counter == 0:
                    property_obj_list, literal_obj_list = self.get_direct_target_path(property_triples=property_triples, path=path)
                    literal_paths += literal_obj_list
                else:
                    property_obj_list = self.get_qualified_target_paths(property_triples=property_triples, path=path)
                
                property_paths += property_obj_list

        property_paths += self.get_inverse_paths(root_node=root_node)

        inherited_property_paths, inherited_literal_paths = self.get_inherited_paths(root_node=root_node)
        property_paths += inherited_property_paths
        literal_paths += inherited_literal_paths
                
        return property_paths, literal_paths

    def get_inherited_nodeshape(self, root_node: rdflib.URIRef):
        inherited_nodeshapes = []

        inherited_triples = self.find_triples(query_subject=root_node,
                                              query_predicate=namespace_provider.SH.node)
        
        min_count = 1
        max_count = 1
        
        for inherited_triple in inherited_triples:
            _, _, inherited_nodeshape_node = inherited_triple
            associated_nodeshape_node = AssociatedNodeShapeNode(nodeshape_node=inherited_nodeshape_node, min_count=min_count, max_count=max_count)
            self.address_constraints(min_count=min_count, max_count=max_count, nodeshape_node_obj=associated_nodeshape_node)
            inherited_nodeshapes.append(associated_nodeshape_node)
        
        return inherited_nodeshapes
    
    def get_path_qualifiedvalue_type(self, qualifiedvalue_shape_node: rdflib.URIRef):
        qualifiedvalue_triples = self.find_triples(query_subject=qualifiedvalue_shape_node)
        qualifiedvalue_attributes = self.get_property_dict(qualifiedvalue_triples)

        if namespace_provider.SH.hasValue in qualifiedvalue_attributes:
            prefix, _, name = self.get_node_values(qualifiedvalue_attributes[namespace_provider.SH.hasValue])
            return f'{prefix}:{name}'
        
        return None
    
    def get_path_nodeshape_types(self, nodeshape_node: rdflib.URIRef):
        all_types = []

        property_triples = self.find_triples(query_subject=nodeshape_node,
                                             query_predicate=namespace_provider.SH.property)
        for property_triple in property_triples:
            _, _, property_node = property_triple

            property_attr_triples = self.find_triples(query_subject=property_node)
            property_attributes = self.get_property_dict(property_attr_triples=property_attr_triples)
            
            if namespace_provider.SH.path in property_attributes:
                if property_attributes[namespace_provider.SH.path] == namespace_provider.RDF.type:
                    if namespace_provider.SH.hasValue in property_attributes:
                        prefix, _, name = self.get_node_values(property_attributes[namespace_provider.SH.hasValue])
                        all_types.append(f'{prefix}:{name}')
                    elif namespace_provider.SH.qualifiedValueShape in property_attributes:
                        all_types.append(self.get_path_qualifiedvalue_type(qualifiedvalue_shape_node=property_attributes[namespace_provider.SH.qualifiedValueShape]))

        return all_types
    
    def get_targetclass_nodeshape_type(self, nodeshape_node: rdflib.URIRef):
        targetclass_node = self.get_targetclass_node(nodeshape_node=nodeshape_node)

        if targetclass_node:
            prefix, _, name = self.get_node_values(targetclass_node)
            return f'{prefix}:{name}'
        else:
            return None

    def get_types_nodeshape(self, nodeshape_node: rdflib.URIRef):
        all_types = []

        all_types += self.get_path_nodeshape_types(nodeshape_node=nodeshape_node)
        all_types.append(self.get_targetclass_nodeshape_type(nodeshape_node=nodeshape_node))
        
        inherited_nodeshapes = self.get_inherited_nodeshape(root_node=nodeshape_node)
        for inherited_nodeshape in inherited_nodeshapes:
            all_types += self.get_types_nodeshape(nodeshape_node=inherited_nodeshape.node)

        return list(set(all_types))
    
class Traverser:
    def __init__(self, g: rdflib.Graph):
        self.shacl_g = g
        self.interpreter = Interpreter(g=g)

    def get_hierarchy(self, root_node: AssociatedNodeShapeNode, is_initial_root: bool = False):
        association_dict = {}

        association_dict['index'] = 'INDEX'
        if not is_initial_root:
            association_dict['parent_index'] = 'PARENTINDEX'
        association_dict['_comment'] = root_node.comment

        associated_nodeshapes, associated_literals = self.interpreter.get_associated_shapes(root_node=root_node.node)

        associated_nodeshapes += self.interpreter.get_inherited_nodeshape(root_node=root_node.node)

        if len(associated_nodeshapes):
            for associated_nodeshape in associated_nodeshapes:
                _, _, nodeshape_name = self.interpreter.get_node_values(node=associated_nodeshape.node)

                if associated_nodeshape.max_count == -1:
                    association_dict[common_util.from_nodeshape_name_to_name(nodeshape_name)] = [self.get_hierarchy(root_node=associated_nodeshape)]
                else:
                    association_dict[common_util.from_nodeshape_name_to_name(nodeshape_name)] = self.get_hierarchy(root_node=associated_nodeshape)

        for literal in associated_literals:
            literal_name = literal.name
            literal_type = literal.type
            association_dict[literal_name] = literal_type.upper()

        return association_dict
    