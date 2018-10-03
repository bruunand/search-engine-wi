from unittest import TestCase

from indexing.indexer import Indexer
from querying.query import Query


class IndexerTests(TestCase):
    def setUp(self):
        self.indexer = Indexer()

        self.indexer.index_text("My name is Anders Langballe Jakobsen. This is a test, test.", 0)
        self.indexer.index_text("This is a unit test for my reverse index implementation", 1)

    def test_frequency_null(self):
        self.assertEqual(2, self.indexer.word_dict.get_frequency_in_document("test", 0))

    def test_and(self):
        self.assertIn(0, Query(self.indexer, 'anders AND langballe').get_matches())

    def test_or(self):
        self.assertEqual(0, len(Query(self.indexer, "NOT test").get_matches()))

    def test_unseen_word(self):
        self.assertEqual(0, len(Query(self.indexer, "unseen").get_matches()))

    def test_parentheses(self):
        self.assertEqual(2, len(Query(self.indexer, "(anders AND langballe) OR (unit AND test)").get_matches()))

    def test_tautology(self):
        self.assertEqual(2, len(Query(self.indexer, "anders OR NOT anders").get_matches()))

    def test_contradiction(self):
        self.assertEqual(0, len(Query(self.indexer, "anders AND NOT anders").get_matches()))
