def _sort_scores(document_scores):
    return sorted(document_scores, key=lambda x: x[1], reverse=True)


class ContentRanker:
    def __init__(self, query, auxiliary_scores=None):
        self._query = query
        self._auxiliary_scores = auxiliary_scores
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
        search_terms = set(self._query.get_search_terms())

        # Find a subset of documents from our champion list
        relevant = set()
        for term in search_terms:
            if term in indexer.term_dict:
                relevant = relevant.union(indexer.term_dict.champion_list[term])

        # Initialize score for each relevant document
        scores = {doc: 0 for doc in relevant}

        # Disregards the frequency of terms in queries and assumes they only occur once
        for term in search_terms:
            for doc in relevant:
                # No need to do a dot product here, since each query term has an equal weight
                scores[doc] += indexer.term_dict.get_tf_idf(term, doc)

        # Normalize scores wrt doc lengths
        # We are not normalizing wrt query lengths because it is a constant, i.e. would not change ordering
        url = indexer.url_vocabulary.get
        scores = [(url(doc), scores[doc] / indexer.term_dict.get_document_length(doc)) for doc in relevant]

        # If we have auxiliary scores, add these
        if self._auxiliary_scores:
            new_scores = []

            for url, score in scores:
                new_scores.append((url, self._auxiliary_scores.get(url, 0)))

            scores = new_scores

        return _sort_scores(scores)

    def top(self, n):
        return self._rank_list[:n]
