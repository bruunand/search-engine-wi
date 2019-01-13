import enum
import re

from stemming.porter2 import stem

from shared.tokenizer import get_disallowed_tokens, doc_preprocess

TokenizerRegex = re.compile(r'(\bAND\b|\bOR\b|NOT|\(|\))')


class TokenType(enum.Enum):
    AND = 0
    OR = 1
    L_PAREN = 2
    R_PAREN = 3
    NOT = 4
    STRING = 5
    ERROR = 6


class BooleanQueryTokenizer:
    def __init__(self, query):
        query = doc_preprocess(query)
        self.index = 0
        self.tokens = [token.strip() for token in TokenizerRegex.split(query) if token.strip() != '']
        self._search_terms = set()
        self._token_types = list()

        for idx, token in enumerate(self.tokens):
            if token == 'AND':
                self._token_types.append(TokenType.AND)
            elif token == 'OR':
                self._token_types.append(TokenType.OR)
            elif token == 'NOT':
                self._token_types.append(TokenType.NOT)
            elif token == '(':
                self._token_types.append(TokenType.L_PAREN)
            elif token == ')':
                self._token_types.append(TokenType.R_PAREN)
            else:
                # Stem string token
                self.tokens[idx] = stem(self.tokens[idx])

                # Remove if disallowed word
                if self.tokens[idx] in get_disallowed_tokens():
                    del self.tokens[idx]

                    continue

                # Add to set of search terms, which is used when doing content ranking
                self._search_terms.add(self.tokens[idx])

                # Add to set of token types, which is used during parsing
                self._token_types.append(TokenType.STRING)

    def get_search_terms(self):
        return self._search_terms

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

        return self._token_types[self.index]

    def is_next_operand(self):
        next_type = self.peek_type()

        return next_type == TokenType.AND or next_type == TokenType.OR
