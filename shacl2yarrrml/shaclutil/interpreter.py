import rdflib
import namespace_provider as namespace_provider


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
    def __init__(self, nodeshape_node: rdflib.URIRef, min_count: int, max_count: int):
        self.node = nodeshape_node
        self.min_count = min_count
        self.max_count = max_count

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
        return self.find_triples(query_predicate=rdflib.URIRef(namespace_provider.RDF.type),
                                 query_object=rdflib.URIRef(namespace_provider.SH.NodeShape))
        
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
            nodeshapes_list.append(AssociatedNodeShapeNode(nodeshape_node=nodeshape_node, min_count=min_count, max_count=max_count))

        elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in qualifiedvalue_attributes:
            class_node = qualifiedvalue_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#class')]
            nodeshape_node = self.from_class_to_nodeshape(class_node=class_node)

            if nodeshape_node:
                nodeshapes_list.append(AssociatedNodeShapeNode(nodeshape_node=nodeshape_node, min_count=min_count, max_count=max_count))

        elif rdflib.URIRef('http://www.w3.org/ns/shacl#or') in qualifiedvalue_attributes:
            or_root_node = qualifiedvalue_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
            self.get_or_nodeshape_nodes(or_root_node=or_root_node, min_count=min_count, max_count=max_count)
            nodeshapes_list += self.get_or_nodeshape_nodes(or_root_node=or_root_node, min_count=min_count, max_count=max_count)

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
                                 min_count=1, max_count=1)  # TODO: fixed
    
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
    
    def get_property_attributes(self, property_triple: tuple):
        _, _, property_node = property_triple

        property_attr_triples = self.find_triples(query_subject=property_node)
        property_attributes = self.get_property_dict(property_attr_triples=property_attr_triples)

        nodeshape_nodes = []
        literals = []

        min_count, max_count = self.get_first_layer_cardinality(property_attributes=property_attributes)

        if namespace_provider.SH.path in property_attributes:
            if property_attributes[namespace_provider.SH.path] != namespace_provider.RDF.type:
                if namespace_provider.SH.node in property_attributes:
                    nodeshape_node = self.get_first_layer_nodeshape(property_attributes=property_attributes)
                    nodeshape_nodes.append(AssociatedNodeShapeNode(nodeshape_node=nodeshape_node, min_count=min_count, max_count=max_count))

                elif rdflib.URIRef('http://www.w3.org/ns/shacl#class') in property_attributes:
                    nodeshape_node = self.get_first_layer_class(property_attributes=property_attributes)
                    nodeshape_nodes.append(AssociatedNodeShapeNode(nodeshape_node=nodeshape_node, min_count=min_count, max_count=max_count))
                    
                elif namespace_provider.SH.qualifiedValueShape in property_attributes:
                    nodeshape_nodes += self.get_qualified_nodeshapes(qualifiedvalue_shape_node=property_attributes[namespace_provider.SH.qualifiedValueShape],
                                                                     property_node=property_node)
                    
                elif namespace_provider.SH.datatype in property_attributes:
                    literals.append(self.get_literal_node(property_attributes=property_attributes))

                elif rdflib.URIRef('http://www.w3.org/ns/shacl#or') in property_attributes:
                    or_root_node = property_attributes[rdflib.URIRef('http://www.w3.org/ns/shacl#or')]
                    nodeshape_nodes += self.get_or_nodeshape_nodes(or_root_node=or_root_node, min_count=min_count, max_count=max_count)
            
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
            nodeshape_nodes, literals = self.get_property_attributes(property_triple=property_triple)
            associated_nodeshapes += nodeshape_nodes
            associated_literals += literals

        return associated_nodeshapes, associated_literals
    
    def get_inherited_nodeshape(self, root_node: rdflib.URIRef):
        inherited_nodeshapes = []

        inherited_triples = self.find_triples(query_subject=root_node,
                                              query_predicate=namespace_provider.SH.node)
        
        for inherited_triple in inherited_triples:
            _, _, inherited_nodeshape_node = inherited_triple
            associated_nodeshape_node = AssociatedNodeShapeNode(nodeshape_node=inherited_nodeshape_node, min_count=1, max_count=1)
            inherited_nodeshapes.append(associated_nodeshape_node)
        
        return inherited_nodeshapes

    def get_hierarchy(self, root_node: rdflib.URIRef):
        association_dict = {}

        associated_nodeshapes, associated_literals = self.get_associated_shapes(root_node=root_node)

        associated_nodeshapes += self.get_inherited_nodeshape(root_node=root_node)

        if len(associated_nodeshapes):
            for associated_nodeshape in associated_nodeshapes:
                _, _, nodeshape_name = self.get_node_values(node=associated_nodeshape.node)

                if associated_nodeshape.max_count == -1:
                    association_dict[nodeshape_name.replace('Shape', '')] = [self.get_hierarchy(root_node=associated_nodeshape.node)]
                else:
                    association_dict[nodeshape_name.replace('Shape', '')] = self.get_hierarchy(root_node=associated_nodeshape.node)

        for literal in associated_literals:
            literal_name = literal.name
            literal_type = literal.type
            association_dict[literal_name] = literal_type.upper()

        return association_dict


