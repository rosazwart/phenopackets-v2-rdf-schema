import rdflib.term
import shacl_loader as shacl_loader
import shacl_interpreter as shacl_interpreter
import namespace_provider as namespace_provider
from ontobio import OntologyFactory
import networkx as nx
import rdflib
import matplotlib.pyplot as plt

def get_in_values(g: rdflib.Graph, o_node):
    has_ended = False
    rest_node = None
    first_node = None

    in_triples = shacl_interpreter.find_triples(g=g, query_subject=o_node)
    for in_triple in in_triples:
        s, p, o = in_triple

        if p == rdflib.URIRef(namespace_provider.RDF.first):
            first_node = o
        
        if p == rdflib.URIRef(namespace_provider.RDF.rest):
            if o == rdflib.URIRef(namespace_provider.RDF.nil):
                has_ended = True
            else:
                rest_node = o

    if has_ended:
        class_objects = []
    else:
        class_objects = get_in_values(g=g, o_node=rest_node)

    if isinstance(first_node, rdflib.term.URIRef):
        class_objects.append(first_node)
    return class_objects


if __name__ == "__main__":
    g = shacl_loader.load_shacl_files()
    triples = shacl_interpreter.find_triples(g=g,
                                             query_predicate=namespace_provider.SH.path)
    
    predicate_g = nx.Graph()
    node_colors = []
    prefix_color = {
        'sio': 'red',
        'phenop': 'black',
        'dcterms': 'blue',
        'obo': 'green'
    }

    predicates = list()
    
    for triple in triples:
        _, _, o = triple
        o_prefix, o_uriref, o_id = g.namespace_manager.compute_qname(o)

        #if o_id not in predicate_g:
        #    node_colors.append(prefix_color[o_prefix])

        #predicate_g.add_node(node_for_adding=o_id, attr={'prefix': o_prefix})

        predicates.append({
            'prefix': o_prefix,
            'uriref': o_uriref,
            'id': o_id
        })

    has_value_triples = shacl_interpreter.find_triples(g=g,
                                                       query_object=namespace_provider.SIO.SIO_000300)
    in_uriref_values = []

    for has_value_triple in has_value_triples:
        s, p, o = has_value_triple

        property_triples = shacl_interpreter.find_triples(g=g, query_subject=s, query_predicate=rdflib.URIRef('http://www.w3.org/ns/shacl#in'))
        for property_triple in property_triples:
            s1, p1, o1 = property_triple

            in_values = get_in_values(g=g, o_node=o1)
            in_uriref_values.extend(in_values)



    for in_uriref_value in in_uriref_values:
        prefix, uriref, id_value = g.namespace_manager.compute_qname(in_uriref_value)
        predicates.append({
            'prefix': prefix,
            'uriref': uriref,
            'id': id_value
        })

    registered_ont_ids = ['ncit', 'sio', 'gsso', 'geno', 'eco', 'maxo']
    ontology_graphs = {}
    for registered_ont_id in registered_ont_ids:
        ofa = OntologyFactory()
        ont = ofa.create(registered_ont_id)
        ont_g = ont.get_graph()
        ontology_graphs[registered_ont_id] = ont_g
    
    print(ontology_graphs)

    for source_predicate in predicates:
        source_ont_id = source_predicate['id'].split('_')[0].lower()

        for target_predicate in predicates:
            target_ont_id = target_predicate['id'].split('_')[0].lower()
            if source_predicate != target_predicate and source_ont_id == target_ont_id:
                
                ont = ontology_graphs[source_ont_id]
                source_node = ont.search(source_predicate['id'].replace('_', ':'))[0]
                target_node = ont.search(target_predicate['id'].replace('_', ':'))[0]


        
        #print('for', id_value)
        #target_node = ont.search(id_value.replace('_', ':'))[0]

        #print(nx.shortest_path_length(ont_g, 'NCIT:C28421', target_node))

    #nx.draw(predicate_g, node_color=node_colors, with_labels=True, pos=nx.spring_layout(predicate_g))
    #plt.show()
    
    #
    #
    #print(ont.search('NCIT:C25393'))
    #
    #print(list(nx.all_simple_paths(G, 'NCIT:C25393', 'NCIT:C25341'))[0:2])




