
from abc import abstractmethod
from enum import Enum
from anytree import Node, RenderTree
from scanner import Token, TokenType
from typing import List, Dict, Set

EPSILON = "EPSILON"

# tree
class ParseTreeNode(object):
    def __init__(self, symbol: str):
        self.symbol = symbol

    @abstractmethod
    def to_anytree(self, parent=None):
        pass


class ParseTreeEpsilonNode(ParseTreeNode):
    def __init__(self, symbol: str):
        super().__init__(symbol)

    def to_anytree(self, parent=None):
        root = Node(self.symbol, parent=parent)
        Node(EPSILON.lower(), parent=root)
        return root


class ParseTreeLeafNode(ParseTreeNode):
    def __init__(self, symbol: str, token: Token):
        super().__init__(symbol)
        self.token = token

    def to_anytree(self, parent=None):
        if self.token.type == TokenType.EOF:
            return Node(self.token.value, parent=parent)
        return Node(f"({self.token.type.value}, {self.token.value})", parent=parent)


class ParseTreeInternalNode(ParseTreeNode):
    def __init__(self, symbol: str, children: List[ParseTreeNode]):
        super().__init__(symbol)
        self.children = children

    def to_anytree(self, parent=None):
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
        if self.error_type == SyntaxErrorType.IllegalSymbol:
            return f"#{self.line_number} : syntax error, illegal {self.symbol}"
        if self.error_type == SyntaxErrorType.MissingSymbol:
            return f"#{self.line_number} : syntax error, missing {self.symbol}"
        if self.error_type == SyntaxErrorType.UnexpectedEOF:
            return f"#{self.line_number} : syntax error, Unexpected EOF"

