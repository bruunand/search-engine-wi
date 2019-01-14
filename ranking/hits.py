import numpy as np

from ranking.content_ranker import ContentRanker


def normalize(vector):
    v_sum = np.sum(vector)

    return [component / v_sum for component in vector]


class HITS:
    # Algorithm with mutually recursive properties
    # Authority scores depends on hub scores of in-links
    # Hub scores depend on authority scores of out-links
    def __init__(self, query, url_references):
        self._url_references = url_references
        self._query = query

    def rank(self, iterations=100):
        # Construct root set
        root_set = [tup[0] for tup in ContentRanker(self._query).top(200)]

        # Construct base set
        base_set = set()
        for referencing in root_set:
            if referencing in self._url_references:
                base_set.update(self._url_references[referencing])

            for other_url, referenced_urls in self._url_references.items():
                if referencing in referenced_urls:
                    base_set.add(other_url)

        # Maintain a mapping from URLs to their index
        url_to_idx = dict()
        for idx, url in enumerate(base_set):
            url_to_idx[url] = idx

        # Initialize a and h values
        a = np.full(len(base_set), 1)
        h = np.full(len(base_set), 1)

        for i in range(iterations):
            # Update authority scores
            # The authority score of a page is the sum of hub scores of pages pointing to it
            for current_url in base_set:
                sum_score = 0

                # Find all URLs referencing this URL
                for referencing, links in self._url_references:
                    if referencing not in base_set:
                        continue

                    for outgoing in links:
                        if outgoing == current_url:
                            # URL points at current URL
                            sum_score += h[url_to_idx[referencing]]

            # Update hub scores
            # The hub score of a page is the sum of authority scores of pages it points to
            for current_url in base_set:
                sum_score = 0
                if current_url not in self._url_references:
                    continue

                # Find all URLs referenced by this URL
                for referenced in self._url_references[current_url]:
                    if referenced in base_set:
                        sum_score += a[url_to_idx[referenced]]

            # Normalize scores
            a = normalize(a)
            h = normalize(h)

        return a, h
