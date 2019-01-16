from nltk import PorterStemmer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

_disallowed_tokens = {'!', '@', '#', '?', ',', '.', '(', ')', '/', '<', '>', '_', '-'}.union(set(stopwords.words('english')))


def get_disallowed_tokens():
    return _disallowed_tokens


def doc_preprocess(text):
    """ Document-wide pre-processing, i.e. not on individual terms """
    # Document is lower-cased and all apostrophes are replaced
    return text.lower().replace('\'', '')


def tokenize(text, remove_stopwords=True, stem_tokens=True):
    # Perform document-wide pre-processing
    text = doc_preprocess(text)

    # Perform tokenization of the text Treebank style
    # Compared to whitespace, punctuation is tokenized
    # This makes it easier to remove such tokens
    tokenized = word_tokenize(text)

    # Remove stopwords if requested
    # In addition, I remove certain symbols (e.g. punctuation)
    if remove_stopwords:
        tokenized = [token for token in tokenized if token not in _disallowed_tokens]

    # Stem tokens if requested
    if stem_tokens:
        stemmer = PorterStemmer()
        tokenized = [stemmer.stem(token) for token in tokenized]

    return tokenized
