import os
import rdflib
import yaml

from shacl_interpreter import find_triples, get_class_object, get_all_nodeshapes
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
        target_class_prefix, _, target_class_name = g.namespace_manager.compute_qname(target_class_node)
       
        obj['mappings'][target_class_name] = {'sources': [{'access': 'FILE.json', 
                                                           'referenceFormulation': 'jsonpath', 
                                                           'iterator': '$.ENTITY[*]'}], 
                                              's': f':{target_class_name.lower()}_$(IDENTIFIER)', 
                                              'po': []}
        
        obj['mappings'][target_class_name]['po'].append(f'[a, {target_class_prefix}:{target_class_name}]')
        
        property_triples = find_triples(g=g,
                                        query_subject=node_shape,
                                        query_predicate=ns.SH.property)
        
        if len(property_triples):
            for property_triple in property_triples:
                s, p, o = property_triple

                property_shape_triples = find_triples(g=g,
                                                    query_subject=o)
                
                object_class = get_class_object(g, property_shape_triples)

                property_obj = {
                    'p': '',
                    'o': {}
                }

                cardinality = ['0', '*']
                property_name = ''

                for property_shape_triple in property_shape_triples:
                    s2, p2, o2 = property_shape_triple

                    if p2 == rdflib.URIRef(ns.SH.path):
                        prefix, _, local_name = g.namespace_manager.compute_qname(o2)
                        property_obj['p'] = f'{prefix}:{local_name}'

                    elif p2 == rdflib.URIRef(ns.SH.datatype):
                        prefix, _, local_name = g.namespace_manager.compute_qname(o2)
                        property_obj['o']['datatype'] = f'{prefix}:{local_name}'

                    elif p2 == rdflib.URIRef(ns.SH.minCount):
                        cardinality[0] = str(o2)

                    elif p2 == rdflib.URIRef(ns.SH.maxCount):
                        cardinality[1] = str(o2)
                    
                    elif p2 == rdflib.URIRef(ns.SH.name):
                        property_name = o2.upper() 
                        if object_class is None:
                            property_obj['o']['value'] = f'$({property_name})'

                if object_class is None:
                    property_obj['o']['value'] += f'[{'..'.join(cardinality)}]'
                else:
                    property_obj['o']['mapping'] = f'{object_class} [{'..'.join(cardinality)}],{property_name}'
                    property_obj['o']['condition'] = {}
                    property_obj['o']['condition']['function'] = 'equal'
                    property_obj['o']['condition']['parameters'] = [f'[str1, $({object_class} SUBJECT ID), s]',
                                                                    f'[str2, $({object_class} OBJECT ID), o]']

                obj['mappings'][target_class_name]['po'].append(property_obj)
        
        else:
            obj['mappings'][target_class_name]['po'] = 'MULTIPLE OPTIONS FOR SETS OF PROPERTIES'    # TODO: Improve handler

    else:
        raise ValueError(f'Missing target class of shape {node_shape}')

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

    nodeshape_triples = get_all_nodeshapes(g)
    for nodeshape_triple in nodeshape_triples:
        s, p, o = nodeshape_triple
        obj = get_shape(obj=obj, g=g, node_shape=s)

    return obj

if __name__ == "__main__":
    shacl_g = load_shacl_files()

    shacl_g = bind_namespaces(shacl_g)

    templ_obj = set_up_template(g=shacl_g)
    dump_to_yaml_file(data_obj=templ_obj)

    # When multiple objects have the same value in their
    # information that is equal to the identifier of
    # subject, then it will have a cardinality of more
    # than one. 
    