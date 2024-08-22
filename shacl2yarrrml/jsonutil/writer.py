import json
import os
import rdflib

import util.common as common_util

import shaclutil.objects as shacl_objects
import shaclutil.interpreter as shacl_interpreter
import shaclutil.traverser as shacl_traverser

class Templater:
    def __init__(self, g: rdflib.Graph):
        """
            Generates JSON template to show the structure that is needed as input for converting data to RDF with YARRRML

            :param g: The RDF graph that represents the SHACL model
            :datatype g: rdflib.Graph
        """
        self.shacl_interpreter = shacl_interpreter.Interpreter(g=g)
        self.shacl_traverser = shacl_traverser.Traverser(g=g)

        self.shacl_g = g

        self.write_files()

    def store_json_file(self, file_name: str, dict_values: dict):
        """ 
            Store JSON file with content from given dictionary.

            :param file_name: Name of the JSON file that will be stored
            :datatype file_name: str

            :param dict_values: Content of the JSON file in dictionary format
            :datatype dict_values: dict
        """
        curr_wdir = os.getcwd()    
        file_path = os.path.join(curr_wdir, 'shacl2yarrrml', 'output', file_name)

        with open(file_path, 'w') as fp:
            json.dump(dict_values, fp, indent=4)

    def write_files(self):
        """
            Write JSON files that are compatible with the generated YARRRML.
        """
        root_nodeshape_nodes = self.shacl_interpreter.get_root_nodeshapes()

        for root_nodeshape_node in root_nodeshape_nodes:
            root_node = shacl_objects.NodeShapeNode(node=root_nodeshape_node, min_count=1, max_count=-1)

            root_dict = self.shacl_traverser.get_hierarchy(root_node=root_node, is_initial_root=True)

            _, _, root_nodeshape_name = self.shacl_interpreter.basic_interpr.extract_values(node=root_node.node)
            nodeshape_label = common_util.from_nodeshape_name_to_name(nodeshape_name=root_nodeshape_name)
            json_dict = {}
            
            json_dict[nodeshape_label] = [root_dict]
            self.store_json_file(file_name=f'{nodeshape_label}.json', dict_values=json_dict)

def create_template(input_g: rdflib.Graph):
    """
        Create JSON templates given the RDF graph representing the SHACL files.

        :param input_g: RDF graph representing the SHACL files
        :datatype input_g: rdflib.Graph
    """
    Templater(g=input_g)
