def _sort_scores(document_scores):
    return sorted(document_scores, key=lambda x: x[1], reverse=True)


class ContentRanker:
    def __init__(self, query):
        self._query = query
        self._rank_list = self._rank_cosine_score()

    def _rank_simple(self):
        scores = dict()
        indexer = self._query.get_indexer()

        # For each doc, calculate its score
        for doc in indexer.indexer.url_vocabulary.get_document_ids():
            score_sum = 0

            for term in self._query.get_search_terms():
                # Since the summation is an interception, ensure that the word is in our indexed corpus
                if not indexer.term_dict.has(term):
                    continue

                term_frequency = indexer.term_dict.get_frequency_log_weighting(term, doc)
                inverse_document_frequency = indexer.term_dict.get_idf(term)

                score_sum += term_frequency - inverse_document_frequency

            scores[doc] = score_sum

        return _sort_scores(scores)

    def _rank_cosine_score(self):
        indexer = self._query.get_indexer()

        # Find the set of relevant documents by disjunction
        relevant = self._query.get_matches()
        scores = {doc: 0 for doc in relevant}

        # Disregards the frequency of terms in queries and assumes they only occur once
        for term in set(self._query.get_search_terms()):
            for doc in relevant:
                scores[doc] += indexer.term_dict.get_tf_idf(term, doc)

        # Normalize scores wrt doc lengths
        # We are not normalizing wrt query lengths because it is a constant, i.e. would not change ordering
        # Thus, we are assuming no weighting no query term and that each query term occurs once
        url = indexer.url_vocabulary.get
        scores = [(url(doc), scores[doc] / indexer.term_dict.get_document_length(doc)) for doc in relevant]

        return _sort_scores(scores)

    def top(self, n):
        return self._rank_list[:n]
