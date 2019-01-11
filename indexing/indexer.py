import math

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
    """ Provide an abstraction over term-postings dictionary """
    def __init__(self, url_vocabulary):
        self._term_postings = dict()
        self._url_vocabulary = url_vocabulary
        self._champion_list = dict()
        self._url_length_dict = dict()

    # The only contender pruning approach I have implemented
    def update_champions(self, r=20):
        self._champion_list = {term: dict() for term in self._term_postings.keys()}

        for term in self._champion_list:
            # Get the docs which this term appears in
            documents = self._term_postings[term].keys()

            # Compute the weights for these docs
            weights = {doc: self.get_tf_idf(term, doc) for doc in documents}

            # Tak the top R of these weights and use this as the champion list for the current term
            self._champion_list[term] = sorted(weights, key=weights.get, reverse=True)[:r]

    def set_term_postings(self, term_postings):
        self._term_postings = term_postings

    def has(self, term):
        return term in self._term_postings

    def set_document_lengths(self, document_length_docs):
        self._url_length_dict = document_length_docs

    """ Calculate the length of a document. """
    def get_document_length(self, document):
        # I originally iterated over the term postings dict and summed
        # That approach was simply too slow
        return self._url_length_dict[document]

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

        if document not in self._term_postings[term]:
            return 0

        return self._term_postings[term][document]

    """ For some word, it will return a set of document IDs that contain the specified word. """
    def get_documents_with_term(self, term):
        if term not in self._term_postings:
            return set()

        return set(self._term_postings[term].keys())


class Indexer:
    def __init__(self):
        self.url_vocabulary = UrlVocabulary()
        self.term_dict = TermDictionary(self.url_vocabulary)

    def index_corpus(self, url_content_dict):
        """ Performs indexing over an entire corpus, e.g. a dictionary from URls to content """
        # At this point, markup has been removed, but we still need to tokenize
        url_token_dict = {url: tokenize(contents) for url, contents in url_content_dict.items()}

        # Add URLs to url vocabulary to get an index representation
        url_index_dict = {url: self.url_vocabulary.add(url) for url in url_token_dict}

        # Make a dictionary of the lengths of documents
        document_length_dict = {url_index_dict[url]: len(tokens) for url, tokens in url_token_dict.items()}
        self.term_dict.set_document_lengths(document_length_dict)

        # Construct (term, docId) pairs
        pairs = list()
        for url, tokens in url_token_dict.items():
            for token in tokens:
                pairs.append((token, url_index_dict[url]))

        # Sort pairs by term, then docId
        # Python automatically does this for lists of pairs
        pairs = sorted(pairs)

        # Construct the dictionary of terms and their postings
        term_postings = dict()

        # Iterate over pairs in order
        current_term = None
        for term, doc_id in pairs:
            # When a new term is found, change current term to it and initialize dictionary
            if term != current_term:
                current_term = term
                term_postings[current_term] = dict()

            # The postings are dictionaries mapping document to frequency
            # We either increment the value part of the posting or set it to 1
            term_postings[term][doc_id] = term_postings[term].get(doc_id, 0) + 1

        self.term_dict.set_term_postings(term_postings)


if __name__ == "__main__":
    # Sanity tests...
    url_contents = {'google.com': 'here is a sample text',
                    'yahoo.com': 'another sample text'}

    indexer = Indexer()
    indexer.index_corpus(url_contents)

    assert(indexer.term_dict.get_df('text') == 2)
    assert(indexer.term_dict.get_document_length(1) == 3)


