from unittest import TestCase

from indexing.indexer import Indexer
from querying.boolean.boolean_query import BooleanQuery
from ranking.content_ranker import ContentRanker


class RankerTests(TestCase):
    def setUp(self):
        indexer = Indexer()

        # Add "URLs" to vocabulary
        for _ in range(3):
            indexer.url_vocabulary.add(None)

        indexer.index_text("This text mentions iPhone twice. iPhone.", 0)
        indexer.index_text("This text mentions iPhone thrice. iPhone, iphone! It should have the highest rank.", 1)
        indexer.index_text("This text only mentions iPhone once.", 2)

        self.query = BooleanQuery(indexer, "iphone")

    def test_simple_order(self):
        rank_iterator = ContentRanker(self.query).top(3)

        self.assertEqual(1, next(rank_iterator))
        self.assertEqual(0, next(rank_iterator))
        self.assertEqual(2, next(rank_iterator))
