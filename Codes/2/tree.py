
from abc import abstractmethod
from enum import Enum
from typing import List
from anytree import Node
from scanner import Token, TokenType

EPSILON = "EPSILON"

class ParseTreeNode(object):
    def __init__(self, symbol: str):
        self.symbol = symbol

    @abstractmethod
    def to_anytree(self, parent=None) -> Node:
        pass

class ParseTreeEpsilonNode(ParseTreeNode):
    def to_anytree(self, parent=None) -> Node:
        root = Node(self.symbol, parent=parent)
        Node(EPSILON.lower(), parent=root)
        return root

class ParseTreeLeafNode(ParseTreeNode):
    def __init__(self, symbol: str, token: Token):
        super().__init__(symbol)
        self.token = token

    def to_anytree(self, parent=None) -> Node:
        if self.token.type == TokenType.EOF:
            return Node(self.token.value, parent=parent)
        return Node(f"({self.token.type.value}, {self.token.value})", parent=parent)

class ParseTreeInternalNode(ParseTreeNode):
    def __init__(self, symbol: str, children: List[ParseTreeNode]):
        super().__init__(symbol)
        self.children = children

    def to_anytree(self, parent=None) -> Node:
        node = Node(f"{self.symbol}", parent=parent)
        for child in self.children:
            if not isinstance(child, ParseTreeSyntaxErrorNode):
                child.to_anytree(parent=node)
        return node

class SyntaxErrorType(Enum):
    IllegalSymbol = 1
    MissingSymbol = 2
    UnexpectedEOF = 3

class ParseTreeSyntaxErrorNode(ParseTreeNode):
    def __init__(self, symbol: str, line_number: int, error_type: SyntaxErrorType):
        super().__init__(symbol)
        self.line_number = line_number
        self.error_type = error_type

    def __str__(self) -> str:
        error_messages = {
            SyntaxErrorType.IllegalSymbol: f"#{self.line_number} : syntax error, illegal {self.symbol}",
            SyntaxErrorType.MissingSymbol: f"#{self.line_number} : syntax error, missing {self.symbol}",
            SyntaxErrorType.UnexpectedEOF: f"#{self.line_number} : syntax error, Unexpected EOF"
        }
        return error_messages.get(self.error_type, "")
    
class ParseTree(object):
    def __init__(self, root: ParseTreeNode):
        self.root = root

    def to_anytree(self) -> Node:
        return self.root.to_anytree()

    def get_errors(self):
        return self.root.get_errors()