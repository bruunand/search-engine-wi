import operator


class ContentRanker():
    def __init__(self, query):
        self._query = query
        self._rank_list = list()
        self._rank_simple()

    def _rank_simple(self):
        document_scores = dict()

        # For each document, calculate its score
        for document in self._query.get_indexer().document_ids:
            score_sum = 0

            for term in self._query.get_search_terms():
                score_sum += self._query.get_indexer().word_dict.get_log_frequency_weight(term, document)

            document_scores[document] = score_sum

        # Sort documents by score and store in internal rank list
        self._rank_list = sorted(document_scores, key=document_scores.get, reverse=True)

    def iterate_documents(self):
        for document in self._rank_list:
            yield document
