import pickle

from indexing.indexer import Indexer
from querying.boolean.boolean_query import BooleanQuery
from querying.free_text_query import FreeTextQuery
from ranking.content_ranker import ContentRanker
from ranking.pagerank import PageRank
from loguru import logger

if __name__ == "__main__":
    # Load corpus from file
    url_contents_dict = pickle.load(open('contents.p', 'rb'))

    # Load URl references from file (used for link analysis)
    url_references = pickle.load(open('references.p', 'rb'))

    # Perform indexing on the corpus
    logger.info(f'Indexing {len(url_contents_dict)} documents')
    indexer = Indexer()
    indexer.index_corpus(url_contents_dict)

    # Save the indexer for fast access
    pickle.dump(indexer, open('indexer.pkl', 'wb'))

    # PageRank the URL references
    logger.info('Performing PageRank')
    page_rank = PageRank(url_references)
    rank_result = page_rank.rank()
    for index, url in enumerate(rank_result[:10]):
        print(f'{index + 1}. {url[0]}')

    # Compute champion list
    logger.info('Updating champion list')
    indexer.term_dict.update_champions(r=20)

    # Make dictionary from URL to PageRank score (for combined score)
    url_pagerank = {tup[0]: tup[1] for tup in rank_result}

    def free_text_mode(query_string, static_rank=None):
        query = FreeTextQuery(indexer, query_string)

        # Rank with cosine score
        content_ranker = ContentRanker(query, static_rank)

        # Print results
        for idx, document in enumerate(content_ranker.top(10)):
            print(f'{idx + 1}. {document[0]}')

    def boolean_query_mode(query_string):
        query = BooleanQuery(indexer, query_string)

        matches = query.get_matches()
        print(f'{len(matches)} matches')
        print(matches)

    # Repeatedly accept user input
    while True:
        query = input('Enter query:')

        logger.info('Without PageRank')
        free_text_mode(query)

        logger.info('With PageRank')
        free_text_mode(query, url_pagerank)
