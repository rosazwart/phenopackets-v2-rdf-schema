import rdflib

used_prefixes = ['sh', 'rdf', 'rdfs', 'xsd', 'dcterms', 'obo', 'sio', 'phenop']

SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')
RDF = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
XSD = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')
DCTERMS = rdflib.Namespace('http://purl.org/dc/terms/')
OBO = rdflib.Namespace('http://purl.obolibrary.org/obo/')
SIO = rdflib.Namespace('http://semanticscience.org/resource/')
PHENOP = rdflib.Namespace('https://phenopackets.org/')

used_namespaces = [SH, RDF, RDFS, XSD, DCTERMS, OBO, SIO, PHENOP]

def bind_namespaces(g: rdflib.Graph):
    for prefix, namespace in zip(used_prefixes, used_namespaces):
        g.bind(prefix, namespace)
    
    return g