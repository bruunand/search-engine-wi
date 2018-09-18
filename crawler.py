import threading
from queue import Queue
import heapq

from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse, urljoin, unquote, urlsplit


def _current_time_millis():
    return datetime.now().microsecond


class BackHeap:
    DeltaTime = 1000  # How long to wait between hitting a host

    def __init__(self):
        self.lock = threading.Lock()
        self.heap = []

    '''
    The heap consists of pairs (time, host) where time specifies when the host can be crawled again.
    Pop host returns a tuple (time_to_wait, host) where time to wait indicates how many seconds before
    the host can be crawled again, allowing the caller to sleep for that duration.
    '''
    def pop_host(self):
        self.lock.acquire()

        try:
            # If heap is empty, return None
            if not self.heap:
                return None

            time, host = heapq.heappop(self.heap)

            # Push the popped host back onto the heap
            # The next crawl time will be our current time + the specified delta time
            heapq.heappush(self.heap, (_current_time_millis() + self.DeltaTime, host))

            # Max is used here to avoid sleeping for a negative duration
            return max(time - _current_time_millis(), 0) / 1000, host
        finally:
            self.lock.release()


class FrontQueue:
    def __init__(self):
        self.urls = dict()
        self.lock = threading.Lock()

    def add_url(self, url):
        self.lock.acquire()

        try:
            # Parse host from URL
            host = urlparse(url).netloc

            # Construct queue for this host
            if host not in self.urls:
                self.urls[host] = Queue()

            self.urls[host].put(url)
        finally:
            self.lock.release()

    def retrieve_url(self, host):
        self.lock.acquire()

        try:
            if host not in self.urls:
                return None

            return self.urls[host].get()
        finally:
            self.lock.release()


class Crawler:
    BaseHeaders = {'User-Agent': 'Kekbot'}
    NumCrawlThreads = 50

    @staticmethod
    def _normalize_url_(url, referer=None):
        # Expand relative links
        if referer:
            url = urljoin(referer, url)

        # Convert protocol and host to lower case
        url = urlsplit(url).geturl()

        # Decode percent-encoded octets of unreserved characters
        url = unquote(url)

        # TODO: Capitalize letters in escape sequences
        # Probably unnecessary, given that the URL is unquoted

        return url


    def __init__(self):
        self.back_heap = BackHeap()
        self.back_queues = dict()
        self.seen_urls = set()

'''
Corners cut: I have not implemented prioritized front queues.
'''