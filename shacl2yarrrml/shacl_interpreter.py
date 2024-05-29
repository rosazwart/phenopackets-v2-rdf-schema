import rdflib
import namespaces as ns

def find_triples(g: rdflib.Graph, query_subject = None, query_predicate = None, query_object = None):
    triple_list = []

    for s, p, o in g.triples((query_subject, query_predicate, query_object)):
        triple_list.append((s, p, o))

    return triple_list

def get_class_object(g: rdflib.Graph, triples):
    object_class_name = None

    for triple in triples:
        s, p, o = triple
        if p == rdflib.URIRef('http://www.w3.org/ns/shacl#class'):
            _, _, object_class_name = g.namespace_manager.compute_qname(o)

        if p == rdflib.URIRef('http://www.w3.org/ns/shacl#or'):
            object_class_name = 'MULTIPLE OPTIONS FOR MAPPED CLASS' # TODO: Improve handler
        

    return object_class_name

def get_all_nodeshapes(g: rdflib.Graph):
    return find_triples(g=g,
                        query_predicate=rdflib.URIRef(ns.RDF.type),
                        query_object=rdflib.URIRef(ns.SH.NodeShape))