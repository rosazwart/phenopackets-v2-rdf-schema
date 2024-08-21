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
            Returns `prefix`, `url`, `name` from given node of SHACL graph.

            :param node: Reference to node from SHACL graph
            :datatype node: rdflib.URIRef

            :returns: Values `prefix`, `url`, `name` of node
            :rtype: str | None, str | None, str | None
        """
        try:
            return self.shacl_g.namespace_manager.compute_qname(node)
        except ValueError:
            return None, None, None

    def find_triples(self, query_subject: rdflib.URIRef | None = None, query_predicate: rdflib.URIRef | None = None, query_object: rdflib.URIRef | None = None) -> List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]:
        """
            Find triples that comply with given query.

            :param query_subject: Subject node that needs to be present in the resulting triples (if not given, any subject node is allowed)
            :datatype query_subject: rdflib.URIRef | None

            :param query_predicate: Predicate that needs to be present in the resulting triples (if not given, any predicate is allowed)
            :datatype query_predicate: rdflib.URIRef | None

            :param query_object: Object node that needs to be present in the resulting triples (if not given, any object node is allowed)
            :datatype query_object: rdflib.URIRef | None

            :returns: List of triples that comply with given query
            :rtype: List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]
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

    def get_object_class_nodes(self, class_node: rdflib.URIRef) -> List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]:
        """
            Get triples that indicate the class of an arbitrary node `(any, SH.class, class_node)`.

            :param class_node: Node that represents class
            :datatype class_node: rdflib.URIRef

            :returns: List of triples that comply with the query
            :rtype: List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]
        """
        return self.find_triples(query_predicate=rdflib.URIRef('http://www.w3.org/ns/shacl#class'), query_object=class_node)

    def get_object_nodeshape_nodes(self, nodeshape_node: rdflib.URIRef) -> List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]:
        """
            Get triples that indicate the nodeshape of an arbitrary node `(any, SH.node, nodeshape_node)`.

            :param nodeshape_node: Node that represents nodeshape
            :datatype nodeshape_node: rdflib.URIRef

            :returns: List of triples that comply with the query
            :rtype: List[Tuple[rdflib.URIRef, rdflib.URIRef, rdflib.URIRef]]
        """
        return self.find_triples(query_predicate=rdflib.URIRef('http://www.w3.org/ns/shacl#node'), query_object=nodeshape_node)
        
    def get_targetclass_node(self, nodeshape_node: rdflib.URIRef):
        """
            Get the class of the nodes that follow the given nodeshape.

            :param nodeshape_node: The node in the SHACL graph representing the nodeshape
            :datatype nodeshape_node: rdflib.URIRef

            :returns: If found, the node that represents the class that is targeted by the nodeshape
            :rtype: None | rdflib.URIRef
        """
        targetclass_triples = self.find_triples(query_subject=nodeshape_node, query_predicate=namespace_provider.SH.targetClass)
        if len(targetclass_triples):
            _, _, node_class = targetclass_triples[0]
            return node_class
        else:
            return None

    def get_property_attr_dict(self, property_attr_triples: list):
        """
            Convert triples that are related to the same property to a dictionary with keys being the attributes of this property and the values the objects of the attributes.

            :param property_attr_triples: List of triples that represents the attributes of the property
            :datatype property_attr_triples: list

            :returns: Dictionary storing the attributes and their objects of the property
            :rtype: dict
        """
        property_attr_dict = {}
        for property_attr_triple in property_attr_triples:
            _, attr_predicate, attr_target = property_attr_triple
            property_attr_dict[attr_predicate] = attr_target
        return property_attr_dict
    
    def get_property_path(self, property_attr_dict: dict):
        """
            Get path name of property given the dictionary with attributes of property.
            
            :param property_attr_dict: Dictionary with attributes of property
            :datatype property_attr_dict: dict

            :returns: Path name or nothing
            :rtype: rdflib.URIRef | None
        """
        if namespace_provider.SH.path in property_attr_dict:
            return property_attr_dict[namespace_provider.SH.path]
        else:
            return None
        
    def get_property_cardinality(self, property_attr_dict: dict):
        """
            Get cardinality of property given dictionary containing all attributes of this property.

            :param property_attr_dict: Dictionary with attributes of property
            :datatype property_attr_dict: dict

            :returns: The cardinality, being the expected minimum and maximum
            :rtype: int, int
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
            Get nodeshape node from given node that represents a class. 

            :param class_node: Node representing a class
            :datatype class_node: rdflib.URIRef

            :returns: Node that represents nodeshape targeting given class
            :rtype: rdflib.URIRef
        """
        targetclass_triple = self.find_first_triple(query_predicate=namespace_provider.SH.targetClass, query_object=class_node)
        if targetclass_triple:
            nodeshape_node, _, _ = targetclass_triple
            return nodeshape_node
        else:
            raise Exception(f'Missing information in SHACL: No nodeshape found targeting class node {class_node}.')
        
    def get_nested_nodes(self, root_node: rdflib.URIRef):
        """
            Get all nodes that are nested into a single statement such as OR. Navigate through `first` and `last` nodes in the RDF graph.

            :param root_node: Node that starts the nesting
            :datatype root_node: rdflib.URIRef

            :returns: List of nodes found of type NodeShape or NodeKind
            :datatype: List[Tuple[rdflib.URIRef, rdflib.URIRef]]
        """
        from_root_node_triples = self.find_triples(query_subject=root_node)

        reached_end = False
        first_node = None
        rest_blank_node = None

        for from_root_node_triple in from_root_node_triples:
            _, p, o = from_root_node_triple

            if p == rdflib.URIRef(namespace_provider.RDF.first):
                first_triple = self.find_first_triple(query_subject=o)
                _, property_val, object_node = first_triple

                if property_val == rdflib.URIRef('http://www.w3.org/ns/shacl#class'):
                    first_node = tuple([self.get_nodeshape_node_from_class_node(object_node), rdflib.SH.NodeShape])

                elif property_val == rdflib.SH.node:
                    first_node = tuple([object_node, rdflib.SH.NodeShape])

                elif property_val == rdflib.SH.nodeKind:
                    first_node = tuple([object_node, rdflib.SH.NodeKind])

                else:
                    raise ValueError(f'SHACL interpreter does not recognize node entity in OR statement ({property_val}).')

            elif p == rdflib.URIRef(namespace_provider.RDF.rest):    
                if o == rdflib.URIRef(namespace_provider.RDF.nil):
                    reached_end = True
                else:
                    rest_blank_node = o

        if reached_end:
            nested_nodes = []
        else:
            nested_nodes = self.get_nested_nodes(root_node=rest_blank_node)

        nested_nodes.append(first_node)
        return nested_nodes
    
    def get_target_nodes_from_or_node(self, or_node: rdflib.URIRef, min_count: int, max_count: int, path: list, property_path_name: str | None):
        """
            Get all target nodes from OR statement which can be of type NodeShape or Literal.

            :param or_node: Node that represents the OR statement
            :datatype or_node: rdflib.URIRef

            :param min_count: The minimum cardinality of the property targeting the nodes in the OR statement
            :datatype min_count: int

            :param max_count: The maximum cardinality of the property targeting the nodes in the OR statement
            :datatype max_count: int

            :param path: Current nodeshape hierarchy expressed in list
            :datatype path: list

            :param property_path_name: Path name of property
            :datatype property_path_name: str

            :returns: List of all associated nodeshapes and literal nodes
            :rtype: List[shacl_objects.NodeShapeNode], List[shacl_objects.LiteralNode]
        """
        associated_nodeshape_nodes = []
        associated_literal_nodes = []

        or_target_nodes = self.get_nested_nodes(root_node=or_node)
        for or_target_node in or_target_nodes:
            or_target_node_obj, or_target_node_type = or_target_node
            if or_target_node_type == rdflib.SH.NodeShape:
                associated_nodeshape_nodes.append(shacl_objects.NodeShapeNode(node=or_target_node_obj, property_path=property_path_name, path=path, min_count=min_count, max_count=max_count))
            elif or_target_node_type == rdflib.SH.NodeKind:
                nodekind_prefix, _, nodekind_name = self.extract_values(or_target_node_obj)
                literal_name = property_path_name.split(':')[-1]
                associated_literal_nodes.append(shacl_objects.LiteralNode(path_name=f'{property_path_name}', rel_path=[], literal_type=f'{nodekind_prefix}:{nodekind_name}',
                                                                          min_count=min_count, max_count=max_count))    # relative path is empty due to being a literal accessed via same nodeshape mapping in YARRRML
            else:
                raise ValueError(f'In path {path} for property {property_path_name} a node entity has not been recognized in OR statement.')

        return associated_nodeshape_nodes, associated_literal_nodes

class Interpreter:
    def __init__(self, g: rdflib.Graph):
        self.shacl_g = g
        self.basic_interpr = BasicInterpreter(g=g)

    def comment_or_constraints(self, min_count: int, max_count: int, or_nodeshapes_list: list, or_literals_list: list):
        """
            Add comment to nodeshapes and literal nodes associated with OR statement to specify cardinality.

            :param min_count: The minimum cardinality of the property targeting the nodes of the OR statement
            :datatype min_count: int
            
            :param max_count: The maximum cardinality of the property targeting the nodes of the OR statement
            :datatype max_count: int

            :param or_nodeshapes_list: List of NodeShape nodes of OR statement
            :datatype or_nodeshapes_list: List[shacl_objects.NodeShapeNode]
            
            :param or_literals_list: List of Literal nodes of OR statement
            :datatype or_literals_list: List[shacl_objects.LiteralNode]
        """
        if max_count == -1:
            max_count_str = '*'
        else:
            max_count_str = str(max_count)

        or_node_names = []
        for or_nodeshape in or_nodeshapes_list:
            _, _, or_nodeshape_name = self.basic_interpr.extract_values(node=or_nodeshape.node)
            or_node_names.append(common_util.from_nodeshape_name_to_name(or_nodeshape_name))
        for or_literal in or_literals_list:
            or_node_names.append(or_literal.literal_type.replace(':', '_'))

        for or_nodeshape in or_nodeshapes_list:
            or_nodeshape.comment = f'Provide with cardinality [{min_count}, {max_count_str}] from the following: {' OR '.join(or_node_names)}'
        for or_literal in or_literals_list:
            or_literal.comment = f'Provide with cardinality [{min_count}, {max_count_str}] from the following: {' OR '.join(or_node_names)}'

    def get_all_nodeshapes(self) -> List[rdflib.URIRef]:
        """
            Get all nodeshape nodes found in the SHACL graph.

            :returns: 
            :rtype: List[rdflib.URIRef]
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
            Check whether the given class or nodeshape is referred to by other nodeshapes.

            :param class_node: Node that represents a class
            :datatype class_node: rdflib.URIRef | None

            :param nodeshape_node: Node that represents a nodeshape
            :datatype nodeshape_node: rdflib.URIRef | None

            :returns: Returns a boolean value to indicate whether the given class or nodeshape is referred to by anything else
            :rtype: bool
        """
        to_class_to_nodeshape_triples = []

        if class_node:
            to_class_to_nodeshape_triples += self.basic_interpr.get_object_class_nodes(class_node=class_node)
        if nodeshape_node:
            to_class_to_nodeshape_triples += self.basic_interpr.get_object_nodeshape_nodes(nodeshape_node=nodeshape_node)
        
        if len(to_class_to_nodeshape_triples):
            return True
        else:
            return False
        
    def get_property_path_counter_dict(self, prop_triples: list):
        """
            Count how often the same path is found as property of the same nodeshape.

            :param prop_triples: List of all triples that represent the property associations
            :datatype prop_triples: list

            :returns: Dictionary storing the counts per found property path
            :rtype: dict
        """
        prop_paths_counter_dict = {}

        for prop_triple in prop_triples:
            _, _, prop_node = prop_triple
            prop_attr_triples = self.basic_interpr.find_triples(query_subject=prop_node)
            prop_dict = self.basic_interpr.get_property_attr_dict(prop_attr_triples)
            
            prop_path = self.basic_interpr.get_property_path(prop_dict)
            common_util.add_to_dict_of_counters(dict_values=prop_paths_counter_dict, key=prop_path, add_number=1)

        return prop_paths_counter_dict

    def get_qualifiedvalue_target_nodeshapes(self, prop_dict: dict, path: list, property_path_name: str):
        """
            Get nodeshape targets from qualified value shape.

            :param prop_dict: Dictionary with all attributes of property.
            :datatype prop_dict: dict

            :param path: Current nodeshape hierarchy expressed in list
            :datatype path: list

            :param property_path_name: Path name of property
            :datatype property_path_name: str

            :returns: List of nodeshapes and list of literal nodes
            :rtype: List[shacl_objects.NodeShapeNode], List[shacl_objects.LiteralNode]
        """
        nodeshape_node_list = []
        literal_node_list = []

        min_count, max_count = self.basic_interpr.get_property_cardinality(prop_dict)

        qualifiedvalue_blank_node = prop_dict[namespace_provider.SH.qualifiedValueShape]
        qualifiedvalue_attributes = self.basic_interpr.find_triples(query_subject=qualifiedvalue_blank_node)
        qualifiedvalue_dict = self.basic_interpr.get_property_attr_dict(qualifiedvalue_attributes)

        target_nodeshape_node = None

        if rdflib.URIRef('http://www.w3.org/ns/shacl#or') in qualifiedvalue_dict:
            or_node = qualifiedvalue_dict[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
            or_nodeshape_nodes, or_literal_nodes = self.basic_interpr.get_target_nodes_from_or_node(or_node=or_node, min_count=min_count, max_count=max_count, path=path, property_path_name=property_path_name)
            self.comment_or_constraints(min_count=min_count, max_count=max_count, or_nodeshapes_list=or_nodeshape_nodes, or_literals_list=[])
            nodeshape_node_list += or_nodeshape_nodes
            literal_node_list += or_literal_nodes
        else:
            if namespace_provider.SH.node in qualifiedvalue_dict:
                target_nodeshape_node = qualifiedvalue_dict[namespace_provider.SH.node]

            elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in qualifiedvalue_dict:
                target_class_node = qualifiedvalue_dict[rdflib.URIRef('http://www.w3.org/ns/shacl#class')]
                target_nodeshape_node = self.basic_interpr.get_nodeshape_node_from_class_node(target_class_node)

            if target_nodeshape_node:
                nodeshape_obj = shacl_objects.NodeShapeNode(node=target_nodeshape_node, property_path=property_path_name, path=path, min_count=min_count, max_count=max_count, add_cardinality_comment=True)
                nodeshape_node_list.append(nodeshape_obj)
        
        return nodeshape_node_list, literal_node_list
        
    def get_property_target_nodes(self, property_node: rdflib.URIRef, path_counter_dict: dict, path: list):
        """
            Get the nodeshape- and literal nodes that are targeted by the given property.
            
            :param property_node: Node that represents the property
            :datatype property_node: rdflib.URIRef

            :param path_counter_dict: Dictionary storing the counts per found property path
            :datatype path_counter_dict: dict

            :param path: Current nodeshape hierarchy expressed in list
            :datatype path: list

            :returns: Target nodeshape nodes and literal nodes
            :rtype: List[rdflib.URIRef], List[rdflib.URIRef]
        """
        property_attributes = self.basic_interpr.find_triples(query_subject=property_node)
        prop_dict = self.basic_interpr.get_property_attr_dict(property_attributes)

        target_nodeshape_nodes = []
        target_literal_nodes = []

        if namespace_provider.SH.path in prop_dict:
            path_node = prop_dict[namespace_provider.SH.path]
            path_occurrence = path_counter_dict[path_node]

            property_path_prefix, _, property_path_id = self.basic_interpr.extract_values(node=path_node)
            if property_path_prefix:
                property_path_name = f'{property_path_prefix}:{property_path_id}'
            else:
                property_path_name = None

            if path_occurrence == 1 or (path_occurrence > 1 and namespace_provider.SH.qualifiedValueShape in prop_dict):
                if path_node != namespace_provider.RDF.type:    # Ignore property path RDF.type
                    
                    min_count, max_count = self.basic_interpr.get_property_cardinality(prop_dict)

                    if namespace_provider.SH.qualifiedValueShape in prop_dict:
                        or_nodeshape_nodes, or_literal_nodes = self.get_qualifiedvalue_target_nodeshapes(prop_dict, path, property_path_name)
                        target_nodeshape_nodes += or_nodeshape_nodes
                        target_literal_nodes += or_literal_nodes

                    elif namespace_provider.SH.node in prop_dict:
                        target_nodeshape_node = prop_dict[namespace_provider.SH.node]
                        target_nodeshape_obj = shacl_objects.NodeShapeNode(node=target_nodeshape_node, property_path=property_path_name, path=path, min_count=min_count, max_count=max_count, add_cardinality_comment=True)
                        target_nodeshape_nodes.append(target_nodeshape_obj)

                    elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in prop_dict:
                        target_class_node = prop_dict[rdflib.URIRef('http://www.w3.org/ns/shacl#class')]
                        target_nodeshape_node = self.basic_interpr.get_nodeshape_node_from_class_node(target_class_node)
                        target_nodeshape_obj = shacl_objects.NodeShapeNode(node=target_nodeshape_node, property_path=property_path_name, path=path, min_count=min_count, max_count=max_count, add_cardinality_comment=True)
                        target_nodeshape_nodes.append(target_nodeshape_obj)

                    elif rdflib.URIRef('http://www.w3.org/ns/shacl#or') in prop_dict:
                        or_node = prop_dict[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
                        or_nodeshape_nodes, or_literal_nodes = self.basic_interpr.get_target_nodes_from_or_node(or_node=or_node, min_count=min_count, max_count=max_count, path=path, property_path_name=property_path_name)
                        self.comment_or_constraints(min_count=min_count, max_count=max_count, or_nodeshapes_list=or_nodeshape_nodes, or_literals_list=or_literal_nodes)
                        target_nodeshape_nodes += or_nodeshape_nodes
                        target_literal_nodes += or_literal_nodes

        return target_nodeshape_nodes, target_literal_nodes
        
    def get_associated_nodes(self, from_node: rdflib.URIRef, path: list):
        """
            Given a node, get all nodes that are associated with this node being the target of a property of this node.

            :param from_node: Node of which the associated nodeshapes need to be found
            :datatype from_node: rdflib.URIRef

            :param path: Current nodeshape hierarchy expressed in list
            :datatype path: list

            :returns: List of associated nodeshape nodes and associated literal nodes
            :rtype: List[rdflib.URIRef], List[rdflib.URIRef]
        """
        from_node_property_triples = self.basic_interpr.find_triples(query_subject=from_node, query_predicate=namespace_provider.SH.property)
        path_counter_dict = self.get_property_path_counter_dict(prop_triples=from_node_property_triples)

        associated_nodeshapes = []
        associated_literals = []

        for property_triple in from_node_property_triples:
            _, _, property_node = property_triple
            target_nodeshapes, target_literals = self.get_property_target_nodes(property_node, path_counter_dict, path)
            associated_nodeshapes += target_nodeshapes
            associated_literals += target_literals

        return associated_nodeshapes, associated_literals
    
    def get_inverse_associated_nodeshapes(self, from_node: rdflib.URIRef, path: list):
        """
            Get nodeshape nodes that are targeted by an inversed property path.

            :param from_node: The node that is the subject of the property path
            :datatype from_node: rdflib.URIRef

            :param path: Current nodeshape hierarchy expressed in list
            :datatype path: list

            :returns: List of associated nodeshapes
            :rtype: List[shacl_objects.NodeShapeNode]
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
            Get nodeshapes that are inherited by the given node.

            :param root_node: The node that inherits the nodeshapes that are found
            :datatype root_node: rdflib.URIRef

            :returns: List of inherited nodeshapes
            :rtype: List[shacl_object.NodeShapeNode]
        """
        inherited_nodeshapes = []
        inherited_triples = self.basic_interpr.find_triples(query_subject=root_node, query_predicate=namespace_provider.SH.node)

        for inherited_triple in inherited_triples:
            _, _, inherited_nodeshape_node = inherited_triple
            inherited_nodeshape_obj = shacl_objects.NodeShapeNode(node=inherited_nodeshape_node, add_cardinality_comment=True)
            inherited_nodeshapes.append(inherited_nodeshape_obj)

        # TODO:
        or_triples = self.basic_interpr.find_triples(query_subject=root_node, query_predicate=rdflib.URIRef('http://www.w3.org/ns/shacl#or'))  
        inherited_or_nodeshapes = []
        for or_triple in or_triples:
            _, _, or_node = or_triple
            or_target_nodes = self.basic_interpr.get_nested_nodes(root_node=or_node)
            for or_target_node in or_target_nodes:
                or_target_node_obj, or_target_node_type = or_target_node
                
                if or_target_node_type == namespace_provider.SH.NodeShape:
                    inherited_nodeshape_obj = shacl_objects.NodeShapeNode(node=or_target_node_obj, add_cardinality_comment=False, from_or_statement=True)
                    inherited_or_nodeshapes.append(inherited_nodeshape_obj)
        
        self.comment_or_constraints(min_count=1, max_count=1, or_nodeshapes_list=inherited_or_nodeshapes, or_literals_list=[])

        inherited_nodeshapes += inherited_or_nodeshapes

        return inherited_nodeshapes
    
    def get_associated_types(self, from_node: rdflib.URIRef):
        """
            Get associated types of given node.

            :param from_node: Node to which the types need to be associated
            :datatype from_node: rdflib.URIRef

            :returns: List of associated types
            :rtype: List[shacl_objects.TypeNode]
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
            if not inherited_nodeshape.from_or:
                associated_types += self.get_associated_types(inherited_nodeshape.node)

        return associated_types
    
    def get_associated_literals(self, from_node: rdflib.URIRef, rel_path: list, include_inherited: bool = True):
        """
            Get all associated literals expressed in various ways such as a type or nodekind.

            :param from_node: Node to which the literals are associated
            :datatype from_node: rdflib.URIRef

            :param rel_path: Current nodeshape hierarchy expressed in list
            :datatype rel_path: list

            :param include_inherited: States whether to include inherited literals as well coming from inherited nodeshapes
            :datatype include_inherited: bool

            :returns: List of associated literals and literal types
            :rtype: List[shacl_objects.LiteralNode], List[shacl_objects.LiteralTypeNode]
        """
        from_node_property_triples = self.basic_interpr.find_triples(query_subject=from_node, query_predicate=namespace_provider.SH.property)
        associated_literals = []
        associated_literaltypes = []

        for property_triple in from_node_property_triples:
            _, _, property_node = property_triple
            prop_attr_triples = self.basic_interpr.find_triples(query_subject=property_node)
            prop_attr = self.basic_interpr.get_property_attr_dict(prop_attr_triples)

            path = self.basic_interpr.get_property_path(prop_attr)
            path_prefix, _, path_name = self.basic_interpr.extract_values(path)
            
            if namespace_provider.SH.datatype in prop_attr:
                literal_datatype_node = prop_attr[namespace_provider.SH.datatype]
                literal_prefix, _, literal_type = self.basic_interpr.extract_values(literal_datatype_node)
                
                associated_literals.append(shacl_objects.LiteralNode(path_name=f'{path_prefix}:{path_name}', rel_path=rel_path, literal_type=f'{literal_prefix}:{literal_type}'))

            elif path == namespace_provider.RDF.type and namespace_provider.SH.qualifiedValueShape in prop_attr:
                qualifiedvalue_node = prop_attr[namespace_provider.SH.qualifiedValueShape]
                qualifiedvalue_triples = self.basic_interpr.find_triples(query_subject=qualifiedvalue_node)
                qualifiedvalue_attr = self.basic_interpr.get_property_attr_dict(qualifiedvalue_triples)

                if namespace_provider.SH.nodeKind in qualifiedvalue_attr:
                    nodekind_node = qualifiedvalue_attr[namespace_provider.SH.nodeKind]
                    nodekind_prefix, _, nodekind_name = self.basic_interpr.extract_values(nodekind_node)

                    associated_literaltypes.append(shacl_objects.LiteralTypeNode(rel_path=rel_path, nodekind_name=f'{nodekind_prefix}:{nodekind_name}', literal_type=nodekind_name))

            elif namespace_provider.SH.nodeKind in prop_attr:
                nodekind_node = prop_attr[namespace_provider.SH.nodeKind]
                nodekind_prefix, _, nodekind_name = self.basic_interpr.extract_values(nodekind_node)
                
                associated_literals.append(shacl_objects.LiteralNode(path_name=f'{path_prefix}:{path_name}', rel_path=rel_path, literal_type=f'{nodekind_prefix}:{nodekind_name}'))
        
        if include_inherited:
            for inherited_nodeshape in self.get_inherited_nodeshapes(from_node):
                if not inherited_nodeshape.from_or:
                    _, _, inherited_nodeshape_name = self.basic_interpr.extract_values(inherited_nodeshape.node)
                    new_path = deepcopy(rel_path)
                    new_path.append(common_util.from_nodeshape_name_to_name(inherited_nodeshape_name))

                    new_associated_literals, new_associated_literaltypes = self.get_associated_literals(inherited_nodeshape.node, rel_path=new_path, include_inherited=include_inherited)
                    associated_literals += new_associated_literals
                    associated_literaltypes += new_associated_literaltypes

        return associated_literals, associated_literaltypes
    
    def get_root_nodeshapes(self):
        """
            Get all nodeshapes that are not referred to by other nodeshapes in the SHACL graph.
        """
        root_nodeshapes = []

        all_nodeshape_nodes = self.get_all_nodeshapes()
        for nodeshape_node in all_nodeshape_nodes:
            class_node = self.basic_interpr.get_targetclass_node(nodeshape_node)

            if not self.is_referred_node_class_or_shape(class_node=class_node, nodeshape_node=nodeshape_node):
                root_nodeshapes.append(nodeshape_node)

        return root_nodeshapes