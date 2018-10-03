import operator


class ContentRanker():
    def __init__(self, query):
        self._query = query
        self._rank_list = list()
        self._rank_simple()

    def _rank_simple(self):
        document_scores = dict()
        indexer = self._query.get_indexer()

        # For each document, calculate its score
        for document in self._query.get_indexer().document_ids:
            score_sum = 0

            for term in self._query.get_search_terms():
                # Since the summation is an interception, ensure that the word is in our indexed corpus
                if not indexer.word_dict.has(term):
                    continue
                
                term_frequency = indexer.word_dict.get_log_frequency_weight(term, document)
                inverse_document_frequency = indexer.word_dict.get_inverse_document_frequency(term)

                score_sum += term_frequency - inverse_document_frequency

            document_scores[document] = score_sum

        # Sort documents by score and store in internal rank list
        self._rank_list = sorted(document_scores, key=document_scores.get, reverse=True)

    def iterate_documents(self):
        for document in self._rank_list:
            yield document
