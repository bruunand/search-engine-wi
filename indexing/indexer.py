import math
from threading import Thread

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


class TermDictionary:
    def __init__(self, url_vocabulary):
        self._internal_dict = dict()
        self._url_vocabulary = url_vocabulary
        self._champion_list = dict()

    # The only contender pruning approach I have implemented
    def update_champions(self, r=20):
        self._champion_list = {term: dict() for term in self._internal_dict.keys()}

        for term in self._champion_list:
            # Get the docs which this term appears in
            documents = self._internal_dict[term].keys()

            # Compute the weights for these docs
            weights = {doc: self.get_tf_idf(term, doc) for doc in documents}

            # Tak the top R of these weights and use this as the champion list for the current term
            self._champion_list[term] = sorted(weights, key=weights.get, reverse=True)[:r]

    def add_occurrence(self, term, document_id):
        if not self.has(term):
            self._internal_dict[term] = dict()

        # Add document to the term's postings list if not existing
        if document_id not in self._internal_dict[term]:
            self._internal_dict[term][document_id] = 0

        self._internal_dict[term][document_id] += 1

    def has(self, term):
        return term in self._internal_dict

    """ Calculate the length of a document. """
    def get_document_length(self, document):
        length = 0

        for term in self._internal_dict.keys():
            length += self.get_tf(term, document)

        return length

    """ Calculates term frequency–inverse document frequency. """
    def get_tf_idf(self, term, document):
        return self.get_tf(term, document) * self.get_idf(term)

    """ Calculate inverse document frequency. Logging is used to dampen its effect. """
    def get_idf(self, term):
        return math.log10(len(self._url_vocabulary.get_document_ids()) / self.get_df(term))

    """ Get the number of documents that the word appears in. """
    def get_df(self, term):
        return len(self.get_documents_with_term(term))

    """ Calculate log frequency weighting.
        Importance does not increase proportionally with frequency, so we use logging to damper the effect.
    """
    def get_frequency_log_weighting(self, word, document):
        frequency = self.get_tf(word, document)

        return 0 if not frequency else 1 + math.log10(frequency)

    """ Calculate term frequency for some term in some document. """
    def get_tf(self, term, document):
        if not self.has(term):
            return 0

        if document not in self._internal_dict[term]:
            return 0

        return self._internal_dict[term][document]

    """ For some word, it will return a set of document IDs that contain the specified word. """
    def get_documents_with_term(self, term):
        return set(self._internal_dict[term].keys())


class Indexer:
    def __init__(self, unindexed_queue=None):
        self.indexing = False
        self.url_vocabulary = UrlVocabulary()
        self.term_dict = TermDictionary(self.url_vocabulary)
        self.document_ids = set()
        self._unindexed_queue = unindexed_queue

    def index_text(self, contents, document_id):
        if document_id not in self.document_ids:
            self.document_ids.add(document_id)

        # Convert contents to lowercase
        contents = contents.lower()

        # Tokenize document and add tokens to word dictionary
        for token in tokenize(contents):
            self.term_dict.add_occurrence(token, document_id)

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
