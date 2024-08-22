import rdflib

import namespace_provider as namespace_provider
import util.common as common_util

import shaclutil.objects as shacl_objects
import shaclutil.interpreter as shacl_interpreter

class Traverser:
    def __init__(self, g: rdflib.Graph):
        """ 
            When initialized, it traverses through the RDF graph representing the SHACL model and creates a dictionary that represents the hierarchy, associations between entities and class inheritance.

            :param g: The RDF graph representing the SHACL model
            :datatype g: rdflib.Graph
        """
        self.shacl_g = g
        self.interpreter = shacl_interpreter.Interpreter(g=g)

    def _init_assoc_dict(self, is_initial_root: bool, comment: str):
        """
            Initialize dictionary to store associations.

            :param is_initial_root: Determines whether the association dictionary needs to store the index of a parent
            :datatype is_initial_root: bool

            :param comment: Stores the comment that is one of the data fields in the association dictionary
            :datatype comment: str

            :returns: The initialized association dictionary
            :rtype: dict
        """
        assoc_dict = {}

        assoc_dict['index'] = 'INDEX'
        if not is_initial_root:
            assoc_dict['parent_index'] = 'PARENTINDEX'
        assoc_dict['_comment'] = comment

        return assoc_dict
    
    def get_append_dict(self, assoc_dict: dict, assoc_path: str | None):
        """
            Build dictionary that includes the property path prior to adding the associated nodeshape or literal in a next step.

            :param assoc_dict: Dictionary of the nodeshape associations
            :datatype assoc_dict: dict

            :param assoc_path: The property path of the current association. If None, then do not add this level for specifying the property path.
            :datatype str

            :returns: The dictionary to which the associated nodeshape or literal dictionary can be appended
            :rtype: dict
        """
        if assoc_path:
            associated_path_name = common_util.from_property_path_to_name(assoc_path)
            if associated_path_name not in assoc_dict:
                assoc_dict[associated_path_name] = {}
            return assoc_dict[associated_path_name]
        else:
            return assoc_dict

    def get_hierarchy(self, root_node: shacl_objects.NodeShapeNode, is_initial_root: bool = False):
        """
            Get hierarchy of the SHACL model in a recursive way. 

            :param root_node: The current root node to decide its descendant nodes
            :datatype root_node: shacl_objects.NodeShapeNode

            :param is_initial_root: Indicate whether the current node is not a node that is referred to by any other node (initial root) based on the SHACL graph
            :datatype is_initial_root: bool

            :returns: Dictionary that represents the hierarchy of the nodeshapes from the current root node and can be used in the JSON template file
            :rtype: dict
        """

        association_dict = self._init_assoc_dict(is_initial_root, comment=root_node.comment)

        associated_literaltypes = []

        associated_nodeshapes, associated_literals = self.interpreter.get_associated_nodes(from_node=root_node.node, path=[])
        associated_nodeshapes += self.interpreter.get_inherited_nodeshapes(root_node=root_node.node)

        for associated_nodeshape in associated_nodeshapes:
            associated_path = associated_nodeshape.property_path
            dict_to_append = self.get_append_dict(assoc_dict=association_dict, assoc_path=associated_path)

            _, _, associated_nodeshape_name = self.interpreter.basic_interpr.extract_values(node=associated_nodeshape.node)

            if root_node.node == associated_nodeshape.node:
                # If the node is associated with another node of the same nodeshape, do not 
                # create the whole dictionary with all information fields of the same nodeshape 
                # (infinite loop!) but terminate with inserting a dictionary that only contains
                # the index fields in order to link to its datafields defined somewhere else in 
                # the JSON file and the parent index in order to associate with the subject of the
                # association.
                dict_to_append[common_util.from_nodeshape_name_to_name(associated_nodeshape_name)] = self._init_assoc_dict(is_initial_root=False, comment=associated_nodeshape.comment)
            else:
                if associated_nodeshape.max_count == -1:
                    # JSON datafield is a list because multiple entities are allowed to be associated with the subject
                    dict_to_append[common_util.from_nodeshape_name_to_name(associated_nodeshape_name)] = [self.get_hierarchy(root_node=associated_nodeshape)]
                else:
                    # JSON datafield is a dictionary representing a single entity
                    dict_to_append[common_util.from_nodeshape_name_to_name(associated_nodeshape_name)] = self.get_hierarchy(root_node=associated_nodeshape)

        other_associated_literals, other_associated_literaltypes = self.interpreter.get_associated_literals(from_node=root_node.node, rel_path=[], include_inherited=False)
        associated_literaltypes += other_associated_literaltypes
        associated_literals += other_associated_literals
        
        for associated_literaltype in associated_literaltypes:
            value_name = associated_literaltype.nodekind_name.replace(':', '_') # this string formatting is needed to allow YARRRML to be directed to the correct datafield
            association_dict[value_name] = associated_literaltype.literal_type.upper()

        for associated_literal in associated_literals:
            value_name = associated_literal.literal_type.replace(':', '_')
            dict_to_append = self.get_append_dict(assoc_dict=association_dict, assoc_path=associated_literal.path_name)

            if associated_literal.max_count == -1:
                dict_to_append[value_name] = [associated_literal.literal_type.upper()]
            else:
                dict_to_append[value_name] = associated_literal.literal_type.upper()

        return association_dict
