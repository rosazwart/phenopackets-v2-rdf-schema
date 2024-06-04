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

def get_object_class(g: rdflib.Graph, triples):
    object_class_name = None

    for triple in triples:
        s, p, o = triple
        if p == rdflib.URIRef('http://www.w3.org/ns/shacl#class'):
            _, _, object_class_name = g.namespace_manager.compute_qname(o)

        if p == rdflib.URIRef('http://www.w3.org/ns/shacl#or'):
            object_class_name = 'MULTIPLE OPTIONS FOR MAPPED CLASS' # TODO: Improve handler
        

    return object_class_name

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

