import json
import os
import rdflib

import util.common as common_util
import shaclutil.interpreter as shacl_interpreter

class Templater:
    def __init__(self, g: rdflib.Graph):
        self.shacl_interpreter = shacl_interpreter.Interpreter(g=g)
        self.shacl_traverser = shacl_interpreter.Traverser(g=g)

        self.shacl_g = g

        self.write_file()

    def store_json_file(self, file_name: str, dict_values: dict):
        curr_wdir = os.getcwd()    
        file_path = os.path.join(curr_wdir, 'shacl2yarrrml', 'output', file_name)

        with open(file_path, 'w') as fp:
            json.dump(dict_values, fp, indent=4)

    def write_file(self):
        all_nodeshape_nodes = self.shacl_interpreter.get_all_nodeshapes()
        root_nodes = self.shacl_interpreter.find_root_nodeshape(all_nodeshape_nodes=all_nodeshape_nodes)

        for root_node in root_nodes:
            root_nodeshape_obj = shacl_interpreter.AssociatedNodeShapeNode(nodeshape_node=root_node,
                                                                           min_count=1,
                                                                           max_count=-1,
                                                                           comment='Root')
            root_dict = self.shacl_traverser.get_hierarchy(root_node=root_nodeshape_obj, is_initial_root=True)

            _, _, nodeshape_name = self.shacl_interpreter.get_node_values(node=root_node)

            json_dict = {}
            json_dict[common_util.from_nodeshape_name_to_name(nodeshape_name)] = [root_dict]

            self.store_json_file(file_name=f'{common_util.from_nodeshape_name_to_name(nodeshape_name)}.json',
                                 dict_values=json_dict)

def create_template(input_g: rdflib.Graph):
    Templater(g=input_g)
