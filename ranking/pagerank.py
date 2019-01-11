import numpy as np


class PageRank:
    def __init__(self, url_references):
        self.url_references = url_references

    def rank(self, alpha=0.15, max_iterations=100):
        # Ensure that we have some URLs with references
        if not self.url_references:
            return []

        matrix, idx_to_url = self.construct_matrix(alpha=alpha)

        # In initial state, equally probable to visit any other link
        state = np.full(len(idx_to_url), 1 / len(idx_to_url))

        # Iterate until convergence
        for i in range(max_iterations):
            old_state = state
            state = np.matmul(old_state, matrix)

            # Check if state has reached a stationary position
            if np.allclose(state, old_state):
                print(f'PageRank converged at iteration {i}')

                break

        top_indices = np.argsort(state)[::-1]
        top_urls = [(idx_to_url[idx], state[idx]) for idx in top_indices]

        return top_urls

    """ Constructs the transition probability matrix """
    def construct_matrix(self, alpha):
        # Get URLs that have been seen (not necessarily visited)
        urls = self.url_references.keys()  # self.crawler.seen_urls

        # Maintain a mapping from URLs to their index
        url_to_idx = dict()
        for idx, url in enumerate(urls):
            url_to_idx[url] = idx

        # Initialize an NxN matrix (where N = |urls|) with zeros
        matrix = np.zeros((len(urls), len(urls)))

        # For each URL, determine the possibility of transitioning and update the matrix
        for url in urls:
            # Ignore URLs which we do not have references for
            if url not in self.url_references:
                continue

            # Get the references for this URL
            # Intersection used to get only references to URLs that we have visited
            references = self.url_references[url].intersection(urls)

            # Row-wise construction depends on whether the page is dangling
            if not references:
                # Dangling pages have equal probability of visiting any URL
                # This could also be fixed by replacing zero-sum rows in transition probability matrix
                for i in range(len(urls)):
                    matrix[url_to_idx[url]][i] = 1 / len(urls)
            else:
                out_degree = len(references)

                # For each referenced URL, calculate the possibility of visiting it
                for ref_url in references:
                    probability = 1 / out_degree
                    matrix[url_to_idx[url]][url_to_idx[ref_url]] = probability

        # Allow our surfers to randomly surf to unlinked pages
        tp_matrix = np.full(matrix.shape, 1 / len(urls))

        # Provide an invert mapping that can be used to get URl from index
        idx_to_url = {v: k for k, v in url_to_idx.items()}

        # P_PageRank = (1 - alpha) * P + alpha * U
        return (1 - alpha) * matrix + alpha * tp_matrix, idx_to_url
