
from typing import List, Dict, Set
from scanner import Token, TokenType
from codegen import CodeGenerator
from tree import ParseTreeNode, ParseTreeEpsilonNode, ParseTreeLeafNode, ParseTreeInternalNode, ParseTreeSyntaxErrorNode, SyntaxErrorType
from grammar import Production, Grammar


EPSILON = "EPSILON"


class ParseTree(object):
    def __init__(self, root: ParseTreeNode):
        self.root = root

    def to_anytree(self):
        return self.root.to_anytree()

    def get_errors(self):
        return self.root.get_errors()

# productios, first, follow ...
def compile_productions():
    productions = []
    for line in open("grammar/grammar.txt"):
        line = line.strip()
        lhs, rhs_raw = line.split(" -> ")
        rhs = [r.split(" ") for r in rhs_raw.split(" | ")]
        productions.append(Production(lhs, rhs))
    for rhs in productions[0].rhs:
        rhs.append("$")
    return productions, productions[0].lhs

def get_terminals_and_non_terminals_and_actions(productions):
    non_terminals = {production.lhs for production in productions}
    terminals = set()
    actions = set()
    for production in productions:
        for rhs in production.rhs:
            for symbol in rhs:
                if symbol not in non_terminals:
                    if symbol.startswith("#"):
                        actions.add(symbol)
                    else:
                        terminals.add(symbol)
    terminals.add("$")
    return terminals, non_terminals, actions


def get_firsts():
    with open("grammar/first.txt") as f:
        header = f.readline().strip().split()[1:]
        firsts = {}
        for line in f:
            line = line.strip().split()
            symbol = line[0]
            answers = line[1:]
            firsts[symbol] = set(
                header[i] for i, answer in enumerate(answers) if answer == "+"
            )
    return firsts

def get_follows():
    with open("grammar/follow.txt") as f:
        header = f.readline().strip().split()[1:]
        follows = {}
        for line in f:
            line = line.strip().split()
            symbol = line[0]
            answers = line[1:]
            follows[symbol] = set(
                header[i] for i, answer in enumerate(answers) if answer == "+"
            )
    return follows

def get_grammar():
    productions, start_symbol = compile_productions()
    terminals, non_terminals, actions = get_terminals_and_non_terminals_and_actions(productions)
    firsts = get_firsts()
    follows = get_follows()
    return Grammar(productions, start_symbol, terminals, non_terminals, firsts, follows, actions)

# parser
class Parser(object):
    def __init__(self, lexer):
        self.grammar = get_grammar()
        self.lexer = lexer
        self.errors = []
        # self.semanticErrorMessage = SemanticError(self, lexer)
        self.code_generator = CodeGenerator(self, lexer)
   

    def parse(self):
        self.lexer.get_next_token()
        root, eof = self.parse_node(self.grammar.start_symbol, 0)
        return ParseTree(root), self.errors

    def parse_node(self, parsing_symbol, depth):
        eof = False
        token = self.lexer.get_current_token()
        if self.grammar.is_terminal(parsing_symbol): # terminal
            if ( # symbol
                (
                    token.type in [TokenType.KEYWORD, TokenType.SYMBOL, TokenType.EOF]
                    and token.value == parsing_symbol
                )
                or (token.type == TokenType.NUM and parsing_symbol == "NUM")
                or (token.type == TokenType.ID and parsing_symbol == "ID")
                or (parsing_symbol == "$")
            ):
                if token.type == TokenType.ID:
                    self.code_generator.last_id = token.value
                if token.type == TokenType.NUM:
                    self.code_generator.last_num = token.value
                if token.type == TokenType.KEYWORD and token.value in ['int', 'void']:
                    self.code_generator.last_type = token.value
                self.lexer.get_next_token()

                if (parsing_symbol == "$"):
                    return ParseTreeLeafNode(parsing_symbol, Token(TokenType.EOF, "$")), False
                return ParseTreeLeafNode(parsing_symbol, token), False
            else: # error
                error = ParseTreeSyntaxErrorNode(
                    parsing_symbol, self.lexer.lineno, SyntaxErrorType.MissingSymbol
                )
                self.errors.append(error)
                return error, False
        else: # non-terminal
            production = self.grammar.get_productions(parsing_symbol)
            for rhss in production.rhs:
                entry_tokens = self.grammar.entry_tokens_for_rhs(parsing_symbol, rhss)
                if ( # check
                    (
                        token.type
                        in [TokenType.KEYWORD, TokenType.SYMBOL, TokenType.EOF]
                        and token.value in entry_tokens
                    )
                    or (token.type == TokenType.NUM and "NUM" in entry_tokens)
                    or (token.type == TokenType.ID and "ID" in entry_tokens)
                ):
                    if len(rhss) == 1 and rhss[0] == EPSILON:
                        return ParseTreeEpsilonNode(parsing_symbol), False
                    children = []
                    for i in range(len(rhss)):
                        # print(rhss[i])
                        if self.grammar.is_action(rhss[i]):
                            self.code_generator.code_gen(rhss[i])
                        else:
                            sub_root, eof = self.parse_node(rhss[i], depth + 1)
                            children.append(sub_root)
                            if eof:
                                break
                    return ParseTreeInternalNode(parsing_symbol, children), eof
            if token.value in self.grammar.get_follow(parsing_symbol): #follow error
                error = ParseTreeSyntaxErrorNode(
                    parsing_symbol, self.lexer.lineno, SyntaxErrorType.MissingSymbol
                )
                self.errors.append(error)
                return error, False
            else: #error
                if token.type == TokenType.EOF:#error
                    error = ParseTreeSyntaxErrorNode(
                        token.value, self.lexer.lineno, SyntaxErrorType.UnexpectedEOF
                    )
                    self.errors.append(error)
                    return error, True
                self.errors.append(
                    ParseTreeSyntaxErrorNode(
                        token.type.value
                        if token.type in [TokenType.NUM, TokenType.ID]
                        else token.value,
                        self.lexer.lineno,
                        SyntaxErrorType.IllegalSymbol,
                    )
                )
                if token.value != ">":
                    self.errors.append(
                        ParseTreeSyntaxErrorNode(
                            token.type.value
                            if token.type in [TokenType.NUM, TokenType.ID]
                            else token.value,
                            self.lexer.lineno,
                            SyntaxErrorType.IllegalSymbol,
                        )
                    )
                if token.type == TokenType.KEYWORD and token.value == "break":
                    self.code_generator.code_gen("break_error")
                self.lexer.get_next_token() #next
                sub_root, eof = self.parse_node(parsing_symbol, depth)
                return sub_root, eof



