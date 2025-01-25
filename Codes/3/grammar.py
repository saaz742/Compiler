from typing import List, Dict, Set

EPSILON = "EPSILON"

class Production(object):
    def __init__(self, lhs: str, rhs: List[List[str]]):
        self.lhs = lhs
        self.rhs = rhs

    def has_epsilon(self):
        for rhs in self.rhs:
            if len(rhs) == 1 and rhs[0] == EPSILON:
                return True
        return False

class Grammar(object):
    def __init__(
        self,
        productions: List[Production],
        start_symbol: str,
        terminals: List[str],
        non_terminals: List[str],
        firsts: Dict[str, Set[str]],
        follows: Dict[str, Set[str]],
        actions: List[str]
    ):
        self.productions = productions
        self.start_symbol = start_symbol
        self.terminals = terminals
        self.non_terminals = non_terminals
        self.firsts = firsts
        self.follows = follows
        self.actions = actions

    def get_productions(self, lhs: str):
        for production in self.productions:
            if production.lhs == lhs:
                return production

    def get_non_terminals(self):
        return self.non_terminals

    def get_terminals(self):
        return self.terminals
    
    def get_first(self, symbol):
        if self.is_terminal(symbol):
            return {symbol}
        return self.firsts[symbol]

    def get_follow(self, symbol):
        return self.follows[symbol]

    def get_actions(self):
        return self.actions
    
    def is_non_terminal(self, symbol):
        return symbol in self.get_non_terminals()

    def is_terminal(self, symbol):
        return symbol in self.get_terminals()

    def is_epsilon(self, symbol):
        return symbol == EPSILON

    def is_start_symbol(self, symbol):
        return symbol == self.start_symbol
    
    def is_action(self, symbol):
        return symbol in self.get_actions()
    
    def filter_actions(self, rhs):
        return [symbol for symbol in rhs if not self.is_action(symbol)]
    
    def entry_tokens_for_rhs(self, lhs: str, rhs: List[str]):
        entry_tokens = set([EPSILON])
        for symbol in self.filter_actions(rhs):
            entry_tokens.remove(EPSILON)
            first = self.get_first(symbol)
            entry_tokens.update(first)
            if EPSILON not in first:
                break
        if EPSILON in entry_tokens:
            entry_tokens.remove(EPSILON)
            entry_tokens.update(self.get_follow(lhs))
        return entry_tokens
