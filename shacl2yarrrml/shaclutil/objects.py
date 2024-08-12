import rdflib


class NodeShapeNode:
    def __init__(self, node: rdflib.URIRef, property_path: str | None = None, path: list = [], min_count: int = 1, max_count: int = 1, comment: str = ''):
        self.node = node
        self.property_path = property_path
        self.path = path
        self.min_count = min_count
        self.max_count = max_count
        self.comment = comment

    def print_node(self):
        print('Node:', self.node, 'Property path:', self.property_path, ', Path:', self.path, ', MinMax:', self.min_count, self.max_count, f'({self.comment})')

class LiteralNode:
    def __init__(self, path_name: str, rel_path: list, literal_name: str, literal_type: str, min_count: int = 1, max_count: int = 1, comment: str = ''):
        self.literal_name = literal_name
        self.rel_path = rel_path
        self.literal_type = literal_type
        self.path_name = path_name
        self.min_count = min_count
        self.max_count = max_count
        self.comment = comment

class LiteralTypeNode:
    def __init__(self, rel_path: list, nodekind_name: str, literal_type: str):
        self.rel_path = rel_path
        self.nodekind_name = nodekind_name
        self.literal_type = literal_type

class TypeNode:
    def __init__(self, type_name: str):
        self.type_name = type_name