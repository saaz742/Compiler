from enum import Enum
from typing import NamedTuple

KEYWORDS = sorted(['if', 'else', 'void', 'int', 'for', 'break', 'endif', 'return'])
SYMBOLS = [';', ':', ',', '[', ']', '(', ')', '{', '}', '+', '-', '*', '=', '<', '==']
is_invalid_char = lambda x: x not in SYMBOLS and not x.isalnum() and not x.isspace() and x != '/'

def write_to_file(filename, data, no_error_msg='There is no lexical error.'):
    with open(filename, 'w') as f:
        if all(len(data[l]) == 0 for l in data):
            f.write(no_error_msg)
        else:
            f.writelines([f'{line}.\t{" ".join(map(str, data[line]))} \n' for line in data if data[line]])

def write_output(tokens, errors, symbol_table):
    write_to_file('tokens.txt', tokens)
    write_to_file('lexical_errors.txt', errors)
    with open('symbol_table.txt', 'w') as f:
        f.writelines([f'{i+1}.\t{symbol_table[i]}\n' for i in range(len(symbol_table))])
    

class TokenType(Enum):
    EOF = "EOF"
    NUM = 'NUM'
    ID = 'ID'
    KEYWORD = 'KEYWORD'
    SYMBOL = 'SYMBOL'
    COMMENT = 'COMMENT'
    WHITESPACE = 'WHITESPACE'


class ErrorType(Enum):
    INVALID_INPUT = "Invalid input"
    UNCLOSED_COMMENT = "Unclosed comment"
    UNMATCHED_COMMENT = "Unmatched comment"
    INVALID_NUMBER = "Invalid number"
    NO_ERROR_MESSAGE = "There is no lexical error."

class Token(NamedTuple):
    type: TokenType
    value: str

    def __str__(self) -> str:
        return f'({self.type.value}, {self.value})'
    
class Error(NamedTuple):
    type: ErrorType
    value: str

    def __str__(self) -> str:
        if self.type == ErrorType.UNCLOSED_COMMENT:
            return f'({self.value[:7]}..., {self.type.value})'
        else:
            return f'({self.value}, {self.type.value})'

class Scanner:
    def __init__(self, input_path):
        self.pos = 0
        self.text = None
        self.current_char = None
        self.next_char = None
        self.lineno = 1
        self.is_comment = False
        self.tokens = {}
        self.errors = {}
        self.symbol_table = []
        self.symbol_table.extend(KEYWORDS)
        with open(input_path, "r") as f:
            self.text = f.read()
        self.current_char = self.text[self.pos]

    def scan(self, input_path):
        self.pos = 0
        with open(input_path, 'r') as f:
            self.text = f.read()
        self.current_char = self.text[self.pos]

        self.tokens[self.lineno] = []
        self.errors[self.lineno] = []
        while self.current_char is not None:
            if self.is_newline(self.current_char) :
                self.lineno += 1
                self.tokens[self.lineno] = []
                self.errors[self.lineno] = []
                self.advance()
                continue
            next_token = self.get_next_token()
            if next_token is None:
                continue
            elif isinstance(next_token, Error):
                self.errors[self.lineno].append(next_token)
            else:
                if next_token.type == TokenType.ID:
                    if next_token.value not in self.symbol_table:
                        self.symbol_table.append(next_token.value)
                if next_token.type == TokenType.COMMENT:
                    continue
                self.tokens[self.lineno].append(next_token)

        
        return self.tokens, self.errors, self.symbol_table

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def is_newline(self, char):
        return char == '\n'


    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            if not self.is_newline(self.current_char):
                self.advance()
            else:
                return True
        return False

    def number_handler(self):
        result = ''
        while self.current_char is not None:
            if self.current_char.isdigit():
                result += self.current_char
                self.advance()
            elif self.current_char.isalpha():
                result += self.current_char
                self.advance()
                return Error(ErrorType.INVALID_NUMBER, result)
            else:
                break
        return Token(TokenType.NUM, result)

    def get_next_token(self):
            while True:
                if self.current_char is None:
                    self.current_token = Token(TokenType.EOF, "EPSILON")
                    return self.current_token
                while self.is_newline(self.current_char):
                    self.lineno += 1
                    self.advance()
                next_token = self._get_next_token()
                if next_token is None:
                    continue
                elif next_token.type == TokenType.COMMENT:
                    continue
                break
            self.current_token = next_token
            return next_token

    def get_current_token(self):
        return self.current_token

    def _get_next_token(self):
        result = ''
        while self.current_char is not None:
            # WHITESPACE Handler
            if self.current_char.isspace():
                new_line = self.skip_whitespace()
                if new_line:
                    return None
                continue
                

            # NUM Handler
            elif self.current_char.isdigit():
                return self.number_handler()
            
            # ID and KEYWORD Handler
            elif self.current_char.isalpha():
                while self.current_char is not None:
                    if self.current_char.isalnum():
                        result += self.current_char
                        self.advance()
                    elif self.current_char.isspace() or self.current_char in SYMBOLS:
                        break
                    else:
                        result += self.current_char
                        self.advance()
                        return Error(ErrorType.INVALID_INPUT, result)
                if result in KEYWORDS:
                    return Token(TokenType.KEYWORD, result)
                else:
                    return Token(TokenType.ID, result)
            
            # COMMENT HANDLER
            elif self.current_char == '/':
                result += self.current_char
                self.advance()
                if self.current_char == '*':
                    # COMMENT START
                    self.is_comment = True
                    result += self.current_char
                    self.advance()
                    while self.current_char is not None:
                        result += self.current_char
                        self.advance()
                        if self.current_char == '*':
                            result += self.current_char
                            self.advance()
                            if self.current_char == '/':
                                # COMMENT END
                                result += self.current_char
                                self.is_comment = False
                                self.advance()
                                return Token(TokenType.COMMENT, result)
                    if self.current_char is None and self.is_comment:
                        return Error(ErrorType.UNCLOSED_COMMENT, result)
                else:                    
                    if is_invalid_char(self.current_char):
                        result += self.current_char
                        self.advance()
                    return Error(ErrorType.INVALID_INPUT, result)
            
            # SYMBOL Handler
            elif self.current_char in SYMBOLS:
                result += self.current_char
                self.advance()
                if result == '=':
                    if self.current_char == '=':
                        result += self.current_char
                        self.advance()
                    elif is_invalid_char(self.current_char):
                        result += self.current_char
                        self.advance()
                        return Error(ErrorType.INVALID_INPUT, result)
                elif result == '*':
                    if self.current_char == '/':
                        result += self.current_char
                        self.advance()
                        if not self.is_comment:
                            return Error(ErrorType.UNMATCHED_COMMENT, result)
                    elif is_invalid_char(self.current_char):
                        result += self.current_char
                        self.advance()
                        return Error(ErrorType.INVALID_INPUT, result)

                return Token(TokenType.SYMBOL, result)
            else:
                result += self.current_char
                self.advance()
                return Error(ErrorType.INVALID_INPUT, result)
