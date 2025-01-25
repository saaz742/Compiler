
from typing import List, Dict, Set
from scanner import Token, TokenType
from tree import ParseTreeEpsilonNode, ParseTreeLeafNode, ParseTreeInternalNode, ParseTreeSyntaxErrorNode, SyntaxErrorType, ParseTree
from grammar import Production, Grammar

EPSILON = "EPSILON"

def compile_grammar() -> Grammar:
    def parse_productions() -> List[Production]:
        productions = []
        with open("grammar/grammar.txt") as file:
            for line in file:
                lhs, rhs_raw = line.strip().split(" -> ")
                rhs = [r.split() for r in rhs_raw.split(" | ")]
                productions.append(Production(lhs, rhs))
        productions[0].rhs[0].append("$")
        return productions

    def extract_symbols(productions: List[Production]) -> (Set[str], Set[str]):
        non_terminals = {prod.lhs for prod in productions}
        terminals = {symbol for prod in productions for rhs in prod.rhs for symbol in rhs if symbol not in non_terminals}
        terminals.add("$")
        return terminals, non_terminals

    def parse_firsts() -> Dict[str, Set[str]]:
        with open("grammar/first.txt") as file:
            header = file.readline().strip().split()[1:]
            firsts = {line.split()[0]: {header[i] for i, answer in enumerate(line.split()[1:]) if answer == "+"} for line in file}
        return firsts

    def parse_follows() -> Dict[str, Set[str]]:
        with open("grammar/follow.txt") as file:
            header = file.readline().strip().split()[1:]
            follows = {line.split()[0]: {header[i] for i, answer in enumerate(line.split()[1:]) if answer == "+"} for line in file}
        return follows

    productions = parse_productions()
    start_symbol = productions[0].lhs
    terminals, non_terminals = extract_symbols(productions)
    firsts = parse_firsts()
    follows = parse_follows()
    return Grammar(productions, start_symbol, terminals, non_terminals, firsts, follows)

class Parser:
    def __init__(self, lexer):
        self.grammar = compile_grammar()
        self.lexer = lexer
        self.errors = []

    def parse(self):
        self.lexer.get_next_token()
        root, eof = self.parse_node(self.grammar.start_symbol, 0)
        return ParseTree(root), self.errors

    def parse_node(self, parsing_symbol, depth):
        token = self.lexer.get_current_token()
        if self.grammar.is_terminal(parsing_symbol):
            if self.match_terminal(parsing_symbol, token):
                self.lexer.get_next_token()
                if parsing_symbol == "$":
                    return ParseTreeLeafNode(parsing_symbol, Token(TokenType.EOF, "$")), False
                return ParseTreeLeafNode(parsing_symbol, token), False
            else:
                error = ParseTreeSyntaxErrorNode(parsing_symbol, self.lexer.lineno, SyntaxErrorType.MissingSymbol)
                self.errors.append(error)
                return error, False
        else:
            return self.handle_non_terminal(parsing_symbol, token, depth)

    def match_terminal(self, parsing_symbol, token):
        return (
            (token.type in [TokenType.KEYWORD, TokenType.SYMBOL, TokenType.EOF] and token.value == parsing_symbol) or
            (token.type == TokenType.NUM and parsing_symbol == "NUM") or
            (token.type == TokenType.ID and parsing_symbol == "ID") or
            (parsing_symbol == "$")
        )

    def handle_non_terminal(self, parsing_symbol, token, depth):
        production = self.grammar.get_productions(parsing_symbol)
        for rhss in production.rhs:
            entry_tokens = self.grammar.entry_tokens_for_rhs(parsing_symbol, rhss)
            if self.match_entry_tokens(entry_tokens, token):
                if len(rhss) == 1 and rhss[0] == EPSILON:
                    return ParseTreeEpsilonNode(parsing_symbol), False
                children = []
                for i in range(len(rhss)):
                    sub_root, eof = self.parse_node(rhss[i], depth + 1)
                    children.append(sub_root)
                    if eof:
                        break
                return ParseTreeInternalNode(parsing_symbol, children), eof
        return self.handle_error(parsing_symbol, token, depth)

    def match_entry_tokens(self, entry_tokens, token):
        return (
            (token.type in [TokenType.KEYWORD, TokenType.SYMBOL, TokenType.EOF] and token.value in entry_tokens) or
            (token.type == TokenType.NUM and "NUM" in entry_tokens) or
            (token.type == TokenType.ID and "ID" in entry_tokens)
        )
        return False

    def handle_error(self, parsing_symbol, token, depth):
        if token.value in self.grammar.get_follow(parsing_symbol):
            error = ParseTreeSyntaxErrorNode(parsing_symbol, self.lexer.lineno, SyntaxErrorType.MissingSymbol)
            self.errors.append(error)
            return error, False
        else:
            return self.handle_illegal_symbol_or_eof(token, parsing_symbol, depth)

    def handle_illegal_symbol_or_eof(self, token, parsing_symbol, depth):
        if token.type == TokenType.EOF:
            error = ParseTreeSyntaxErrorNode(token.value, self.lexer.lineno, SyntaxErrorType.UnexpectedEOF)
            self.errors.append(error)
            return error, True
        if token.value != ">":
            self.errors.append(ParseTreeSyntaxErrorNode(
                token.type.value if token.type in [TokenType.NUM, TokenType.ID] else token.value,
                self.lexer.lineno, SyntaxErrorType.IllegalSymbol
            ))
        self.lexer.get_next_token()
        sub_root, eof = self.parse_node(parsing_symbol, depth)
        return sub_root, eof
    
