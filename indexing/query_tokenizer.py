import enum
import re
TokenizerRegex = re.compile(r'(\bAND\b|\bOR\b|NOT|\(|\))')


class TokenType(enum.Enum):
    AND = 0
    OR = 1
    L_PAREN = 2
    R_PAREN = 3
    NOT = 4
    STRING = 5
    ERROR = 6


class Tokenizer:
    def __init__(self, query):
        self.index = 0
        self.tokens = [token.strip() for token in TokenizerRegex.split(query) if token.strip() != '']

        self.token_types = list()
        for token in self.tokens:
            if token == 'AND':
                self.token_types.append(TokenType.AND)
            elif token == 'OR':
                self.token_types.append(TokenType.OR)
            elif token == 'NOT':
                self.token_types.append(TokenType.NOT)
            elif token == '(':
                self.token_types.append(TokenType.L_PAREN)
            elif token == ')':
                self.token_types.append(TokenType.R_PAREN)
            else:
                self.token_types.append(TokenType.STRING)

    def has_next(self):
        return self.index < len(self.tokens)

    def next(self):
        if not self.has_next():
            return None

        self.index += 1
        return self.tokens[self.index - 1]

    def peek(self):
        if not self.has_next():
            return None

        return self.tokens[i]

    def peek_type(self):
        if not self.has_next():
            return TokenType.ERROR

        return self.token_types[self.index]

    def is_next_operand(self):
        next = self.peek_type()

        return next == TokenType.AND or next == TokenType.OR


if __name__ == "__main__":
    tokenizer = Tokenizer('matias AND thomas OR (anders langballe AND morten)')
    print(tokenizer.tokens)
    print(tokenizer.token_types)
