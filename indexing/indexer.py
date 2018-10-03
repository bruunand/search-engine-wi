import math
from threading import Thread

from querying.query import Query
from shared.tokenizer import tokenize


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
        if not self.has(word):
            self._internal_dict[word] = dict()

        # Check if document is part of the dictionary
        if document_id not in self._internal_dict[word]:
            self._internal_dict[word][document_id] = 0

        self._internal_dict[word][document_id] += 1

    def has(self, word):
        return word in self._internal_dict

    """ Calculate idf. Logging is used to dampen its effect. """
    def get_inverse_document_frequency(self, word):
        return math.log10(len(self._url_vocabulary.get_document_ids()) / self.get_document_frequency(word))

    """ Get the number of documents that the word appears in. """
    def get_document_frequency(self, word):
        return len(self.get_documents_with(word))

    """ Importance does not increase proportionally with frequency, so we use logging to damper the effect."""
    def get_log_frequency_weight(self, word, document):
        frequency = self.get_frequency_in_document(word, document)

        return 0 if not frequency else 1 + math.log10(frequency)

    """ For some word, it will return a dictionary of documents IDs to the number of occurrences of that word. """
    def get_frequency_in_document(self, word, document):
        if not self.has(word):
            return 0

        if document not in self._internal_dict[word]:
            return 0

        return self._internal_dict[word][document]

    """ For some word, it will return a set of document IDs that contain the specified word. """
    def get_documents_with(self, word):
        return set(self._internal_dict[word].keys())


class Indexer:
    def __init__(self, unindexed_queue=None):
        self.indexing = False
        self.url_vocabulary = UrlVocabulary()
        self.word_dict = WordDictionary(self.url_vocabulary)
        self.document_ids = set()
        self._unindexed_queue = unindexed_queue

    def index_text(self, contents, document_id):
        if document_id not in self.document_ids:
            self.document_ids.add(document_id)

        # Convert contents to lowercase
        contents = contents.lower()

        # Tokenize document and add tokens to word dictionary
        for token in tokenize(contents):
            self.word_dict.add_occurrence(token, document_id)

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
