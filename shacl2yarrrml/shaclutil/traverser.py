import rdflib
from copy import deepcopy

import namespace_provider as namespace_provider
import util.common as common_util

import shaclutil.objects as shacl_objects
import shaclutil.interpreter as shacl_interpreter

class Traverser:
    def __init__(self, g: rdflib.Graph):
        self.shacl_g = g
        self.interpreter = shacl_interpreter.Interpreter(g=g)

    def get_hierarchy(self, root_node: shacl_objects.NodeShapeNode, is_initial_root: bool = False):
        """
        """
        association_dict = {}

        association_dict['index'] = 'INDEX'
        if not is_initial_root:
            association_dict['parent_index'] = 'PARENTINDEX'
        association_dict['_comment'] = root_node.comment

        associated_literaltypes = []
        associated_nodeshapes, associated_literals = self.interpreter.get_associated_nodeshapes(from_node=root_node.node, path=[])
        associated_nodeshapes += self.interpreter.get_inherited_nodeshapes(root_node=root_node.node)

        for associated_nodeshape in associated_nodeshapes:
            _, _, associated_nodeshape_name = self.interpreter.basic_interpr.extract_values(node=associated_nodeshape.node)
            
            if associated_nodeshape.max_count == -1:
                association_dict[common_util.from_nodeshape_name_to_name(associated_nodeshape_name)] = [self.get_hierarchy(root_node=associated_nodeshape)]
            else:
                association_dict[common_util.from_nodeshape_name_to_name(associated_nodeshape_name)] = self.get_hierarchy(root_node=associated_nodeshape)

        other_associated_literals, other_associated_literaltypes = self.interpreter.get_associated_literals(from_node=root_node.node, rel_path=[], include_inherited=False)
        associated_literaltypes += other_associated_literaltypes
        associated_literals += other_associated_literals
        
        for associated_literaltype in associated_literaltypes:
            value_name = associated_literaltype.nodekind_name.replace(':', '_')
            association_dict[value_name] = associated_literaltype.literal_type.upper()

        for associated_literal in associated_literals:
            value_name = associated_literal.literal_name.replace(':', '_')

            if associated_literal.max_count == -1:
                association_dict[value_name] = [associated_literal.literal_type.upper()]
            else:
                association_dict[value_name] = associated_literal.literal_type.upper()

        return association_dict
