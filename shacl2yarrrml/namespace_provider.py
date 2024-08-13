import rdflib

SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')
RDF = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
XSD = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')

def bind_namespaces(g: rdflib.Graph, prefixes: dict):
    """
        Bind declared prefixes to namespace in given RDF graph.
        :param g: RDF graph
        :datatype g: rdflib.Graph
        :param prefixes: Dictionary with declared prefixes as keys and values being the namespace strings
        :datatype prefixes: dict
    """

    for prefix in prefixes:
        namespace = prefixes[prefix]
        g.bind(prefix, namespace)
        