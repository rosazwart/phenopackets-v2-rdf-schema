import json
import os
import rdflib

import util.common as common_util
import shaclutil.objects as shacl_objects
import shaclutil.interpreter as shacl_interpreter
import shaclutil.traverser as shacl_traverser

class Templater:
    def __init__(self, g: rdflib.Graph):
        self.shacl_interpreter = shacl_interpreter.Interpreter(g=g)
        self.shacl_traverser = shacl_traverser.Traverser(g=g)

        self.shacl_g = g

        self.write_files()

    def store_json_file(self, file_name: str, dict_values: dict):
        curr_wdir = os.getcwd()    
        file_path = os.path.join(curr_wdir, 'shacl2yarrrml', 'output', file_name)

        with open(file_path, 'w') as fp:
            json.dump(dict_values, fp, indent=4)

    def write_files(self):
        root_nodeshape_nodes = self.shacl_interpreter.get_root_nodeshapes()

        for root_nodeshape_node in root_nodeshape_nodes:
            root_node = shacl_objects.NodeShapeNode(node=root_nodeshape_node, min_count=1, max_count=-1)

            root_dict = self.shacl_traverser.get_hierarchy(root_node=root_node, is_initial_root=True)

            _, _, root_nodeshape_name = self.shacl_interpreter.basic_interpr.extract_values(node=root_node.node)

            json_dict = {}
            json_dict[common_util.from_nodeshape_name_to_name(nodeshape_name=root_nodeshape_name)] = [root_dict]

            self.store_json_file(file_name=f'{common_util.from_nodeshape_name_to_name(nodeshape_name=root_nodeshape_name)}.json', dict_values=json_dict)

def create_template(input_g: rdflib.Graph):
    Templater(g=input_g)
