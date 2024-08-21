import rdflib

SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')
RDF = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = rdflib.Namespace('http://www.w3.org/2000/01/rdf-schema#')
XSD = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')

# Prefixes for PhenopacketsV2
DCTERMS = rdflib.Namespace('http://purl.org/dc/terms/')
OBO = rdflib.Namespace('http://purl.obolibrary.org/obo/')
SIO = rdflib.Namespace('http://semanticscience.org/resource/')
PHENOP = rdflib.Namespace('http://purl.org/ejp-rd/phenopackets-rdf-schema/v200/shacl/')
EX = rdflib.Namespace('https://example.org/')

# Prefixes for FDP
FDP = rdflib.Namespace('http://fairdatapoint.org/')
DASH = rdflib.Namespace('http://datashapes.org/dash#')
DCAT = rdflib.Namespace('http://www.w3.org/ns/dcat#')
DCT = rdflib.Namespace('http://purl.org/dc/terms/')
LDP = rdflib.Namespace('http://www.w3.org/ns/ldp#')
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

#used_prefixes = ['sh', 'rdf', 'rdfs', 'xsd', 'dct', 'obo', 'sio', 'phenop', 'ex']
#used_namespaces = [SH, RDF, RDFS, XSD, DCTERMS, OBO, SIO, PHENOP, EX]
#entity_prefix = 'ex'

used_prefixes = ['fdp', 'dash', 'dcat', 'dct', 'sh', 'xsd']
used_namespaces = [FDP, DASH, DCAT, DCT, SH, XSD]
entity_prefix = 'fdp'

def bind_namespaces(g: rdflib.Graph):
    for prefix, namespace in zip(used_prefixes, used_namespaces):
        g.bind(prefix, namespace)
    
    return g