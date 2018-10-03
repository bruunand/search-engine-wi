from unittest import TestCase

from indexing.indexer import Indexer
from querying.query import Query
from ranking.content_ranker import ContentRanker


class RankerTests(TestCase):
    def setUp(self):
        indexer = Indexer()
        indexer.index_text("This text mentions iPhone twice. iPhone.", 0)
        indexer.index_text("This text mentions iPhone thrice. iPhone, iphone! It should have the highest rank.", 1)
        indexer.index_text("This text only mentions iPhone once.", 2)

        self.query = Query(indexer, "iphone")

    def test_simple_order(self):
        rank_iterator = ContentRanker(self.query).iterate_documents()

        self.assertEqual(1, next(rank_iterator))
        self.assertEqual(0, next(rank_iterator))
        self.assertEqual(2, next(rank_iterator))
