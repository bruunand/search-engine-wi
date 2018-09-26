from unittest import TestCase

from indexing.indexer import Indexer


class IndexerTests(TestCase):
    def setUp(self):
        self.indexer = Indexer()

        self.indexer.index_text("My name is Anders Langballe Jakobsen", 0)
        self.indexer.index_text("This is a unit test for my reverse index implementation", 1)

    def test_and(self):
        self.assertIn(0, self.indexer.query('anders AND langballe'))

    def test_or(self):
        self.assertEqual(0, len(self.indexer.query("NOT is")))

    def test_unseen_word(self):
        self.assertEqual(0, len(self.indexer.query("unseen")))

    def test_parentheses(self):
        self.assertEqual(2, len(self.indexer.query("(anders AND langballe) OR (unit AND test)")))

    def test_tautology(self):
        self.assertEqual(2, len(self.indexer.query("anders OR NOT anders")))

    def test_contradiction(self):
        self.assertEqual(0, len(self.indexer.query("anders AND NOT anders")))

