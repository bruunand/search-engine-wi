import pickle

from indexing.indexer import Indexer
from querying.free_text_query import FreeTextQuery
from ranking.content_ranker import ContentRanker
from ranking.pagerank import PageRank

if __name__ == "__main__":
    # Load corpus from file
    url_contents_dict = pickle.load(open('contents.p', 'rb'))

    # Load URl references from file (used for link analysis)
    url_references = pickle.load(open('references.p', 'rb'))

    # Perform indexing on the corpus
    indexer = Indexer()
    indexer.index_corpus(url_contents_dict)

    # PageRank the URL references
    page_rank = PageRank(url_references)
    for url, probability in page_rank.rank()[:10]:
        print(f'{probability}: {url}')

    # Iteratively accept user input
    while True:
        query_string = input('Enter free text query:')

        # Construct query
        query = FreeTextQuery(indexer, query_string)
        print(query.get_matches())

        # Rank with cosine score
        content_ranker = ContentRanker(query)

        # Print results
        for document, score in content_ranker.top(10):
            print(f'{score}: {document}')
