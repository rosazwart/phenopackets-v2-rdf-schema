import rdflib


class NodeShapeNode:
    def __init__(self, node: rdflib.URIRef, property_path: str | None = None, path: list = [], min_count: int = 1, max_count: int = 1, add_cardinality_comment: bool = False, from_or_statement: bool = False):
        """
            Store node that represents a nodeshape.

            :param node: Stores reference to node that represents a nodeshape
            :datatype node: rdflib.URIRef

            :param property_path: If nodeshape is target of a property, this stores the name of this property path
            :datatype property_path: str | None

            :param path: If nodeshape is target of a property, this stores the nodeshape hierarchy towards this target
            :datatype path: list

            :param min_count: If nodeshape is target of a property, this stores the cardinality regarding the minimum of this property pointing towards the nodeshape
            :datatype min_count: int

            :param max_count: If nodeshape is target of a property, this stores the cardinality regarding the maximum of this property pointing towards the nodeshape (use -1 for *)
            :datatype max_count: int

            :param add_cardinality_comment: Indicates whether a comment about the cardinality needs to be expressed in JSON files
            :datatype add_cardinality_comment: bool
        """
        self.node = node
        self.property_path = property_path
        self.path = path
        self.min_count = min_count
        self.max_count = max_count

        self.from_or = from_or_statement
        
        self.comment = ''

        if add_cardinality_comment:
            self.comment_constraints()

    def comment_constraints(self):
        """
            Add comment related to cardinality of property path towards this nodeshape.
        """
        if self.max_count == -1:
            max_count_str = '*'
        else:
            max_count_str = str(self.max_count)

        self.comment = f'[{self.min_count}, {max_count_str}]'

class LiteralNode:
    def __init__(self, path_name: str, rel_path: list, literal_type: str, min_count: int = 1, max_count: int = 1, comment: str = ''):
        """
            Store node that represents a literal that is the object of a property.

            :param path_name: Name of the path of property
            :datatype path_name: str

            :param rel_path: The hierarchy of nodeshapes towards this literal stored in a list
            :datatype rel_path: list

            :param literal_type: The given datatype name
            :datatype literal_type: str

            :param min_count: Stores the cardinality regarding the minimum of this property pointing towards the literal
            :datatype min_count: int

            :param max_count: Stores the cardinality regarding the maximum of this property pointing towards the literal (use -1 for *)
            :datatype max_count: int

            :param comment: Comment
            :datatype comment: str
        """
        self.rel_path = rel_path
        self.literal_type = literal_type
        self.path_name = path_name
        self.min_count = min_count
        self.max_count = max_count
        self.comment = comment

class LiteralTypeNode:
    def __init__(self, rel_path: list, nodekind_name: str, literal_type: str):
        """
            Stores node that represents the literal expressed as a type of a node.

            :param rel_path: The hierarchy of nodeshapes towards this literal stored in a list
            :datatype rel_path: list

            :param nodekind_name: The name of the nodekind which is the literal type
            :datatype nodekind_name: str

            :param literal_type: The label of the literal type
            :datatype literal_type: str
        """
        self.rel_path = rel_path
        self.nodekind_name = nodekind_name
        self.literal_type = literal_type

class TypeNode:
    def __init__(self, type_name: str):
        """
            Stores node that represents the type of a node

            :param type_name: The name of the type
            :datatype type_name: str
        """
        self.type_name = type_name