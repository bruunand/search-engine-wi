import functools

from stemming.porter2 import stem
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

_disallowed_tokens = {'!', '@', '#', '?', ',', '.', '(', ')', '/', '<', '>'}.union(set(stopwords.words('english')))


def doc_preprocess(text):
    """ Document-wide pre-processing, i.e. not on individual terms """
    return text.lower()


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
    if stem:
        tokenized = [stem(token) for token in tokenized]

    return tokenized
