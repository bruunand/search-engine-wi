from shared.tokenizer import tokenize


class FreeTextQuery:
    def __init__(self, indexer, query):
        self._indexer = indexer
        self._tokens = tokenize(query)
        self._matches = self._get_matches()

    def _get_matches(self):
        """ Eagerly computed early on, then stored locally """
        matches = set()

        for term in self._tokens:
            matches = matches.union(self._indexer.term_dict.get_documents_with_term(term))

        return matches

    def get_indexer(self):
        return self._indexer

    def get_search_terms(self):
        return self._tokens

    def get_matches(self):
        return self._matches
