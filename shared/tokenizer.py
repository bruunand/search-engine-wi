from stemming.porter2 import stem
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

_disallowed_words = {'!', '?', ',', '.', '(', ')', '/', '<', '>'}.union(set(stopwords.words('english')))


def get_disallowed_words():
    return _disallowed_words


def tokenize(text):
    """ Tokenizes and stems word that are not in the set of disallowed words """
    return [stem(word) for word in word_tokenize(text) if word not in get_disallowed_words()]

