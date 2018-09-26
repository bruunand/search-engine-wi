from threading import Thread
import re

from querying.querier import Querier


class UrlVocabulary:
    """
    UrlVocabulary assigns a document ID to URLs and points to the URL
    """
    def __init__(self):
        self._document_counter = -1
        self._internal_dict = dict()

    def get_document_ids(self):
        return set(self._internal_dict.keys())

    def add(self, url):
        # Check if URL is already in dictionary (may not be necessary, NOT efficient)
        for key, value in self._internal_dict.items():
            if value == url:
                return key

        # Add URL and its content to dictionary
        self._document_counter += 1
        self._internal_dict[self._document_counter] = url

        return self._document_counter

    def get(self, id):
        return self._internal_dict[id] if id in self._internal_dict else None


class WordDictionary:
    def __init__(self, url_vocabulary):
        self._internal_dict = dict()
        self._url_vocabulary = url_vocabulary

    def add_occurrence(self, word, document_id):
        if word not in self._internal_dict:
            self._internal_dict[word] = set()

        self._internal_dict[word].add(document_id)

    def has(self, word):
        return word in self._internal_dict

    def get(self, word):
        return self._internal_dict[word]


def tokenize(text):
    split = text.split()

    return split


class Indexer:
    def __init__(self, unindexed_queue=None):
        self.indexing = False
        self.url_vocabulary = UrlVocabulary()
        self.word_dictionary = WordDictionary(self.url_vocabulary)
        self.document_ids = set()
        self._unindexed_queue = unindexed_queue

    def index_text(self, contents, document_id):
        if not document_id in self.document_ids:
            self.document_ids.add(document_id)

        # Convert contents to lowercase
        contents = contents.lower()

        # Tokenize document and add tokens to word dictionary
        for token in tokenize(contents):
            self.word_dictionary.add_occurrence(token, document_id)

    """Performs indexing in the background"""
    def start_indexer(self):
        self.indexing = True

        def _indexer():
            while self.indexing:
                url, contents = self._unindexed_queue.get()

                # Get document id
                document_id = self.url_vocabulary.add(url)

                self.index_text(contents, document_id)

        thread = Thread(target=_indexer)
        thread.start()

    def stop_indexer(self):
        self.indexing = False

    """ Returns a set of document IDs which match the query. """
    def query(self, query):
        querier = Querier(self)

        return querier.parse_query(query)
