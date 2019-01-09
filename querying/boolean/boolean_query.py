from querying.boolean.boolean_query_tokenizer import BooleanQueryTokenizer, TokenType


class BooleanQuery:
    def __init__(self, indexer, query):
        self._indexer = indexer
        self._tokenizer = BooleanQueryTokenizer(query)
        self._search_terms = self._tokenizer.get_search_terms()
        self._matches = self._parse()

    def get_indexer(self):
        return self._indexer

    def get_matches(self):
        return self._matches

    def get_search_terms(self):
        return self._search_terms

    def _parse(self):
        while self._tokenizer.has_next():
            peek = self._tokenizer.peek_type()

            negate = peek == TokenType.NOT
            if negate:
                self._tokenizer.next()

            current_term = self._parse_term()
            if negate:
                # Take complement of term
                current_term = self._indexer.document_ids.difference(current_term)

            # Parse from left to right as long as next token is an operand
            while self._tokenizer.is_next_operand():
                operand = self._tokenizer.peek_type()
                if not self._tokenizer.next():
                    raise ValueError('Expected expression after operand')

                next_term = self._parse_term()

                if operand == TokenType.AND:
                    current_term = current_term.intersection(next_term)
                elif operand == TokenType.OR:
                    current_term = current_term.union(next_term)
                else:
                    raise ValueError('Unknown operand')

            return current_term

    def _parse_term(self):
        token_type = self._tokenizer.peek_type()

        if token_type == TokenType.STRING:
            term = self._tokenizer.next().lower()

            return self._indexer.term_dict.get_documents_with_term(term) if self._indexer.term_dict.has(term) else set()
        elif token_type == TokenType.L_PAREN:
            # Proceed to next token
            self._tokenizer.next()

            # Parse expression in parenthesis
            expression = self._parse()

            # We expect an R_PAREN to follow this expression
            if self._tokenizer.peek_type() != TokenType.R_PAREN:
                raise ValueError('Expected right parentheses')

            # Skip right parentheses
            self._tokenizer.next()

            return expression
        elif token_type == TokenType.R_PAREN:
            raise ValueError('Unexpected right parentheses')

        # Not string or parentheses, parse as expression
        return self._parse()
