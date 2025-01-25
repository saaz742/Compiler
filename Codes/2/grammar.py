

from typing import List, Dict, Set

EPSILON = "EPSILON"

class Production:
    def __init__(self, lhs: str, rhs: list[List[str]]):
        self.lhs = lhs
        self.rhs = rhs

    def has_epsilon(self) -> bool:
        return any(len(rhs) == 1 and rhs[0] == EPSILON for rhs in self.rhs)

class Grammar:
    def __init__(
        self,
        productions: List[Production],
        start_symbol: str,
        terminals: Set[str],
        non_terminals: Set[str],
        firsts: Dict[str, Set[str]],
        follows: Dict[str, Set[str]]
    ):
        self.productions = productions
        self.start_symbol = start_symbol
        self.terminals = terminals
        self.non_terminals = non_terminals
        self.firsts = firsts
        self.follows = follows

    def get_productions(self, lhs: str) -> Production:
        return next((prod for prod in self.productions if prod.lhs == lhs), None)

    def is_non_terminal(self, symbol: str) -> bool:
        return symbol in self.non_terminals

    def is_terminal(self, symbol: str) -> bool:
        return symbol in self.terminals

    def is_epsilon(self, symbol: str) -> bool:
        return symbol == EPSILON

    def is_start_symbol(self, symbol: str) -> bool:
        return symbol == self.start_symbol

    def get_first(self, symbol: str) -> Set[str]:
        return {symbol} if self.is_terminal(symbol) else self.firsts[symbol]

    def get_follow(self, symbol: str) -> Set[str]:
        return self.follows[symbol]

    def entry_tokens_for_rhs(self, lhs: str, rhs: List[str]) -> Set[str]:
        entry_tokens = {EPSILON}
        for symbol in rhs:
            entry_tokens.discard(EPSILON)
            first = self.get_first(symbol)
            entry_tokens.update(first)
            if EPSILON not in first:
                break
        if EPSILON in entry_tokens:
            entry_tokens.discard(EPSILON)
            entry_tokens.update(self.get_follow(lhs))
        return entry_tokens
