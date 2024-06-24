""" 
This module is written to convert any given shacl shape into
a template that corresponds to one instance of the node
described in the shape.
"""

from rdflib import Graph, URIRef, SH, RDF, Literal
import os


#class Node:



class Cop:

    def __init__(self, shape_path="shacl\Phenopacket.ttl", mappings="", data="", fdp_url="fdp-test.lumc.nl/") -> None:
        self.shape_path = shape_path
        self.map = mappings
        self.data = data
        self.shape = Graph().parse(shape_path)
        self.graph = Graph(namespace_manager=self.shape.namespace_manager)
        self.classes = [classes for classes, p, t in self.shape.triples((None, None, SH.NodeShape))]
        self.url = fdp_url


    def extract_properties(self, nodes):
        #TODO: load complete context into graph, AgentShape is only in catalogshape
        """
        Generate a template resource for every node in shape
        """
        for node in nodes:
            print("shape node:")
            print(node)
            node, p, targetClass = self.shape.triples((node, SH.targetClass, None)).__next__()
            print("target class:")
            print(targetClass)
            node_string = Literal(targetClass.n3(self.graph.namespace_manager).rpartition(":")[-1].upper())
            self.graph.add((node_string, RDF.type, targetClass))
            print("properties:")
            for node, p, property in self.shape.triples((node, SH.property, None)):
                crossref = False
                for bnode, node_path, node_type in self.shape.triples((property, SH.node, None)):
                    if node_type in nodes:
                        crossref = True
                for b, p, path in self.shape.triples((property, SH.path, None)):
                    if crossref:
                        self.graph.add((node_type))
                    self.graph.add((node_string, path, Literal(path.n3(self.graph.namespace_manager).rpartition(":")[-1].upper())))

            print(self.graph.serialize())
        self.graph.serialize("data/FDP/output/test_template.ttl")
            #TODO: integrate sh:node to publisher or other properties


    def extract_props_recursive(self, node):
        new_triples = [] # store triples for ttl
        for node, p, classtype in self.shape.triples((node, SH.targetClass, None)): # obtain class definition
             node_string = Literal(classtype.n3(self.graph.namespace_manager).rpartition(":")[-1].upper())
             new_triples.append((node_string, RDF.type, classtype, self.graph))
        for p_node, p, property in self.shape.triples((node, SH.property, None)): # go through all checked class properties
            for b, p, path in self.shape.triples((property, SH.path, None)): # for every class property, make a triple with placeholder strings
                property_string = Literal(path.n3(self.graph.namespace_manager).rpartition(":")[-1].upper())
                new_triples.append((node_string, path, property_string, self.graph))
            for b_node, node_path, node_type in self.shape.triples((property, SH.node, None)): # if a property is a node/class get the requirements of that class and link that to the property_string
                    if node_type in self.classes:
                        dummy_name, triples = self.extract_props_recursive(node_type)
                        triples.append((property_string, RDF.type, dummy_name, self.graph))
                        new_triples.extend(triples)
        
        print(classtype)
        return node_string, new_triples


    def parse_shape(self):
        nodes = []
        for s, p, o in self.shape.triples((None, None, SH.NodeShape)):
            nodes.append(s)
        self.extract_properties(nodes)
    

    def generate_graph(self):
        self.shape.serialize("schema/shacl/CatalogShape.ttl")
        self.shape.serialize("data/FDP/output/test_shape.ttl")
        #TODO: generate a serialization(s) that has KEYWORDS to be used in string replacement to fill data into the desired shape.
        pass


    def chain_data(self, shape, map, data):
        """
        Fill template with corresponding data
        """
        pass
    



if __name__ == '__main__':
    catalog = Cop()
    #catalog.generate_graph()
    #catalog.parse_shape()
    node_string, triples = catalog.extract_props_recursive(catalog.classes[0])
    catalog.graph.addN(triples)
    print(catalog.graph.serialize())
    catalog.graph.serialize("test_template.ttl")
