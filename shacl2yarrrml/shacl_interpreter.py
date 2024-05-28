import rdflib
import namespaces as ns

def find_triples(g: rdflib.Graph, query_subject = None, query_predicate = None, query_object = None):
    triple_list = []

    for s, p, o in g.triples((query_subject, query_predicate, query_object)):
        triple_list.append((s, p, o))

    return triple_list

def is_class_object(triples):
    is_class = False

    for triple in triples:
        predicate = triple[1]
        if predicate == rdflib.URIRef('http://www.w3.org/ns/shacl#class'):
            is_class = True

    return is_class

def get_all_nodeshapes(g: rdflib.Graph):
    return find_triples(g=g,
                        query_predicate=rdflib.URIRef(ns.RDF.type),
                        query_object=rdflib.URIRef(ns.SH.NodeShape))