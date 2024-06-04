import rdflib
import namespace_provider as namespace_provider

def find_triples(g: rdflib.Graph, query_subject = None, query_predicate = None, query_object = None):
    triple_list = []

    for s, p, o in g.triples((query_subject, query_predicate, query_object)):
        triple_list.append((s, p, o))

    return triple_list

def get_property_dict(g: rdflib.Graph, property_triples: list):
    property_dict = {
        'path': None,
        'datatype': None,
        'minCount': '0',
        'maxCount': '*',
        'name': None
    }

    for property_triple in property_triples:
        s, p, o = property_triple

        if p == rdflib.URIRef(namespace_provider.SH.path):
            prefix, _, local_name = g.namespace_manager.compute_qname(o)
            property_dict['path'] = f'{prefix}:{local_name}'

        elif p == rdflib.URIRef(namespace_provider.SH.datatype):
            prefix, _, local_name = g.namespace_manager.compute_qname(o)
            property_dict['datatype'] = f'{prefix}:{local_name}'

        elif p == rdflib.URIRef(namespace_provider.SH.minCount):
            property_dict['minCount'] = str(o)

        elif p == rdflib.URIRef(namespace_provider.SH.maxCount):
            property_dict['maxCount'] = str(o)

        elif p == rdflib.URIRef(namespace_provider.SH.name):
            property_dict['name'] = o.lower()
    
    return property_dict

def get_or_object_class(g: rdflib.Graph, or_node: rdflib.URIRef):
    triples = find_triples(g=g, query_subject=or_node)
    
    or_has_ended = False
    or_rest_node = None
    or_first_node = None

    for triple in triples:
        s, p, o = triple

        if p == rdflib.URIRef(namespace_provider.RDF.first):
            or_first_node = o
        
        if p == rdflib.URIRef(namespace_provider.RDF.rest):
            if o == rdflib.URIRef(namespace_provider.RDF.nil):
                or_has_ended = True
            else:
                or_rest_node = o

    if or_has_ended:
        class_objects = []
    else:
        class_objects = get_or_object_class(g=g, or_node=or_rest_node)
    
    first_node_triples = find_triples(g=g, query_subject=or_first_node)
    if len(first_node_triples):
        if first_node_triples[0][1] == rdflib.URIRef('http://www.w3.org/ns/shacl#class'):
            _, _, class_object_name = g.namespace_manager.compute_qname(first_node_triples[0][2])
            class_objects.append(class_object_name)

    return class_objects

def get_object_class(g: rdflib.Graph, triples: list):
    object_class_name = None

    for triple in triples:
        s, p, o = triple
        if p == rdflib.URIRef('http://www.w3.org/ns/shacl#class'):
            _, _, object_class_name = g.namespace_manager.compute_qname(o)

        if p == rdflib.URIRef('http://www.w3.org/ns/shacl#or'):
            class_objects = get_or_object_class(g=g, or_node=o)
            object_class_name = '|'.join(class_objects)
        
    return object_class_name

def get_xone_property(g: rdflib.Graph, xone_node: rdflib.URIRef):
    triples = find_triples(g=g, query_subject=xone_node)

    xone_has_ended = False
    xone_rest_node = None
    xone_first_node = None

    for triple in triples:
        s, p, o = triple

        if p == rdflib.URIRef(namespace_provider.RDF.first):
            xone_first_node = o
        
        if p == rdflib.URIRef(namespace_provider.RDF.rest):
            if o == rdflib.URIRef(namespace_provider.RDF.nil):
                xone_has_ended = True
            else:
                xone_rest_node = o

    if xone_has_ended:
        property_nodes = []
    else:
        property_nodes = get_xone_property(g=g, xone_node=xone_rest_node)
    
    first_node_triples = find_triples(g=g, query_subject=xone_first_node)
    if len(first_node_triples):
        property_nodes.append(first_node_triples[0][2])

    return property_nodes

def get_xone_properties(g: rdflib.Graph, triples: list):
    properties = []
    for triple in triples:
        s, p, o = triple

        if p == rdflib.URIRef('http://www.w3.org/ns/shacl#xone'):
            properties = get_xone_property(g=g, xone_node=o)
            
    return properties

def get_properties(g: rdflib.Graph, node_shape: rdflib.URIRef):
    return find_triples(g=g,
                        query_subject=node_shape,
                        query_predicate=namespace_provider.SH.property)

def get_target_class(g: rdflib.Graph, node_shape: rdflib.URIRef):
    return find_triples(g=g, 
                        query_subject=node_shape,
                        query_predicate=namespace_provider.SH.targetClass)

def get_all_nodeshapes(g: rdflib.Graph):
    return find_triples(g=g,
                        query_predicate=rdflib.URIRef(namespace_provider.RDF.type),
                        query_object=rdflib.URIRef(namespace_provider.SH.NodeShape))

