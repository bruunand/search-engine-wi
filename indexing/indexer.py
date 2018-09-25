from threading import Thread


class UrlVocabulary:
    """
    UrlVocabulary assigns a document ID to URLs and points to the URL
    """
    def __init__(self):
        self._document_counter = -1
        self._internal_dict = dict()

    def get_document_ids(self):
        return set(self._internal_dict.keys())

    def add_url(self, url):
        # Check if URL is already in dictionary (may not be necessary, NOT efficient)
        for key, value in self._internal_dict.items():
            if value == url:
                return key

        # Add URL and its content to dictionary
        self._document_counter += 1
        self._internal_dict[self._document_counter] = url

        return self._document_counter


class WordDictionary:
    def __init__(self, url_vocabulary):
        self._internal_dict = dict()
        self._url_vocabulary = url_vocabulary

    def add_word_occurrence(self, word, document_id):
        if word not in self._internal_dict:
            self._internal_dict[word] = set()

        self._internal_dict[word].add(document_id)

    def has(self, word):
        return word in self._internal_dict

    def get(self, word):
        return self._internal_dict[word]


def tokenize(text):


class Indexer:
    def __init__(self, unindexed_queue):
        self._indexer_thread = None
        self._unindexed_queue = unindexed_queue
        self._url_vocabulary = UrlVocabulary()
        self._word_dictionary = WordDictionary(self._url_vocabulary)

    """Performs indexing in the background"""
    def run(self):
        def _indexer():
            while True:
                url, contents = self._unindexed_queue.get()

                # Get document id
                document_id = self._url_vocabulary.add_url(url)

                # Convert contents to lowercase
                contents = contents.lower()


                # Tokenize document and add tokens to word dictionary
                for token in tokenize(contents):
                    self._word_dictionary.add_word_occurrence(token, document_id)
                # Split to get every word
                for word in contents.split():
                    self._word_dictionary.add_word_occurrence(word, document_id)

                print(self._word_dictionary._internal_dict)

        self._indexer_thread = Thread(target=_indexer)
        self._indexer_thread.start()

    def _term_to_set(self, term):
        # Parse term in parentheses
        # Parse AND term
        # Parse OR term
        # Parse NOT term
        # It is most likely a word, lookup which documents it appears in
        # If it is not in the word dictionary, return the empty set
        return self._word_dictionary.get(term) if self._word_dictionary.has(term) else set()

    def _not(self, term):
        return self._url_vocabulary.get_document_ids().difference(term)

    def _and(self, left, right):
        return left.intersection(right)

    def _or(self, left, right):
        return left.union(right)
