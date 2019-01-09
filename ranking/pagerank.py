from copy import deepcopy

import networkx as nx
import numpy as np


class PageRank:
    def __init__(self, crawler):
        self.crawler = crawler

    def rank(self):
        graph, idx_to_url = self.construct_graph()
        pr = nx.pagerank(graph, alpha=0.85)  # 0.15 probability of teleportation

        return {idx_to_url[idx]: value for idx, value in pr.items()}

    """ Constructs the directed graph to be used by NetworkX. """
    def construct_graph(self):
        # Get URLs that have been seen (not necessarily visited)
        urls = deepcopy(self.crawler.seen_urls)

        # Maintain a mapping from URLs to their index
        url_to_idx = dict()
        for idx, url in enumerate(urls):
            url_to_idx[url] = idx

        # Construct graph with edges
        graph = nx.DiGraph()

        # For each URL, add an edge to its outgoing URLs
        for idx, url in enumerate(urls):
            # Ignore URLs which we do not have references for
            if url not in self.crawler.url_references:
                continue

            references = self.crawler.url_references[url]
            # Ignore URLs which reference no URLs
            if not references:
                continue

            # For each referenced URL, add an edge from current URL to that URL
            for ref_url in references:
                graph.add_edge(idx, url_to_idx[ref_url])

        # Return the graph and an index to url mapping
        return graph, {idx: url for url, idx in url_to_idx.items()}

    """ Constructs the transition probability matrix. """
    def construct_matrix(self):
        # Get URLs that have been seen (not necessarily visited)
        urls = self.crawler.seen_urls

        # Maintain a mapping from URLs to their index
        url_to_idx = dict()
        for idx, url in enumerate(urls):
            url_to_idx[url] = idx

        # Initialize an NxN matrix (where N = |urls|) with zeros
        matrix = np.zeros((len(urls), len(urls)))

        # For each URL, determine the possibility of transitioning and update the matrix
        for url in urls:
            # Ignore URLs which we do not have references for
            if url not in self.crawler.url_references:
                continue

            references = self.crawler.url_references[url]
            # Ignore URLs which reference no URLs
            if not references:
                continue

            out_degree = len(references)

            # For each referenced URL, calculate the possibility of visiting it
            for ref_url in references:
                matrix[url_to_idx[url]][url_to_idx[ref_url]] = 1 / out_degree
                print(matrix[url_to_idx[url]][url_to_idx[ref_url]])

        return matrix
