import os
import rdflib
import yaml

from shacl_interpreter import find_triples, is_class_object
import namespaces as ns

def load_shacl_files(dir_name: str = 'shacl'):
    curr_wdir = os.getcwd()

    g = rdflib.Graph()

    for file_name in os.listdir(dir_name):
        file_path = os.path.join(curr_wdir, dir_name, file_name)
        if os.path.isfile(file_path):
            print('Add SHACL shapes from', file_name)
            g.parse(file_path)

    print('RDF graph with SHACL shapes created from directory', os.path.join(curr_wdir, dir_name))

    return g

def dump_to_yaml_file(data_obj: dict):
    with open('phenopacket_template.yaml', 'w') as yaml_file:
        yaml.dump(data_obj, yaml_file, default_flow_style=False, sort_keys=False)

def get_shape(obj: dict, g: rdflib.Graph, node_shape: rdflib.URIRef):

    target_class_triples = find_triples(g=g, 
                                        query_subject=node_shape,
                                        query_predicate=ns.SH.targetClass)
    
    if len(target_class_triples):
        target_class_node = target_class_triples[0][2]
        _, _, target_class_name = g.namespace_manager.compute_qname(target_class_node)
       
        obj['mappings'][target_class_name] = {'sources': [{'access': '', 'referenceFormulation': '', 'iterator': ''}], 
                                              's': [], 
                                              'po': []}
    else:
        raise ValueError(f'Missing target class of shape {node_shape}')
    
    property_triples = find_triples(g=g,
                                    query_subject=node_shape,
                                    query_predicate=ns.SH.property)
    
    for property_triple in property_triples:
        s, p, o = property_triple

        property_obj = {
            'p': '',
            'o': {}
        }

        property_shape_triples = find_triples(g=g,
                                              query_subject=o)
        
        is_class = is_class_object(property_shape_triples)

        for property_shape_triple in property_shape_triples:
            print(property_shape_triple)

            

    
    '''

    for s, p, o in g.triples((node_shape, SH.property, None)):


        if g.triples((o, rdflib.URIRef('http://www.w3.org/ns/shacl#class'), None)):
            print(o)

        for s1, p1, o1 in g.triples((o, None, None)):
            print(s1, p1, o1)

            #if p1 == rdflib.URIRef(SH.path):
            #    print(s1, p1, o1)


    '''

    return obj

def bind_namespaces(g: rdflib.Graph):
    for prefix, namespace in zip(ns.used_prefixes, ns.used_namespaces):
        g.bind(prefix, namespace)
    
    return g

def set_up_template(g: rdflib.Graph):
    obj = {
            'prefixes': {},
            'mappings': {}
    }

    for prefix, namespace in g.namespaces():
        if prefix in ns.used_prefixes:
            obj['prefixes'][prefix] = str(namespace)


    obj = get_shape(obj=obj, g=g, node_shape=rdflib.URIRef(ns.PHENOP.PhenopacketShape))

    return obj

if __name__ == "__main__":
    shacl_g = load_shacl_files()

    shacl_g = bind_namespaces(shacl_g)

    templ_obj = set_up_template(g=shacl_g)
    dump_to_yaml_file(data_obj=templ_obj)
    