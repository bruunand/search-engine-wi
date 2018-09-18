from bs4 import BeautifulSoup
from datetime import datetime


class Crawler:
    BaseHeaders = {'User-Agent': 'Kekbot'}
    NumCrawlThreads = 50

    @staticmethod
    def _current_time_millis():
        return datetime.now().microsecond

    @staticmethod
    def _normalize_url_(url, referer=None):
        # Expand relative links
        # Convert protocol and host to lower case
        # Capitalize letters in escape sequences
        # Decode percent-encoded octets of unreserved characters
        pass

    def __init__(self):
        self.host_hit_times = dict()
        self.seen_urls = set()

