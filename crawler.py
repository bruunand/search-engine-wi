import heapq
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging import getLogger
from queue import Queue
from time import sleep
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
        with self.lock:
            # If heap is empty, return None
            if not self.heap:
                return None

            time, host = heapq.heappop(self.heap)

            # Push the popped host back onto the heap
            # The next crawl time will be our current time + the specified delta time
            heapq.heappush(self.heap, (_current_time_millis() + self.DeltaTime, host))

            # Max is used here to avoid sleeping for a negative duration
            return max(time - _current_time_millis(), 0) / 1000, host

    def add_new_host(self, host):
        with self.lock:
            # Extracts hosts from the heap, used to test whether the host is actually new
            hosts = [pair(1) for pair in self.heap]

            if host not in hosts:
                # Add the host to the top of heap, could also use current time instead of zero
                heapq.heappush(self.heap, (0, host))


class FrontQueue:
    def __init__(self):
        self.urls = dict()
        self.lock = threading.Lock()

    def add_url(self, url):
        with self.lock:
            # Parse host from URL
            host = urlparse(url).netloc

            # Construct queue for this host
            if host not in self.urls:
                self.urls[host] = Queue()

            self.urls[host].put(url)

    def retrieve_url(self, host):
        self.lock.acquire()

        with self.lock:
            if host not in self.urls:
                return None

            return self.urls[host].get()


class BackQueue:
    pass


class Crawler:
    BaseHeaders = {'User-Agent': 'Kekbot'}
    MaxCrawlWorkers = 10

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

    def queue_raw_url(self, url):
        # Normalize URL
        url = self._normalize_url_(url)

        # If we have seen this URL, discard it
        with self.lock:
            if url in self.seen_urls:
                return
            else:
                self.seen_urls.add(url)

        # If host is unseen, create back queue and heap entry
        host = urlparse(url).netloc
        if host not in self.back_queues:
            self.back_queues[host] = BackQueue()
            self.back_heap.add_new_host(host)

    '''
    Runs a number of crawlers which will run indefinitely. 
    '''
    def run_crawlers(self):
        # Could principally not be a nested function, but it's nested to discourage calling from main thread
        def _crawl_():
            while True:
                # Get next host to crawl and time we need to wait
                heap_pair = self.back_heap.pop_host()

                # It should not occur that there are no hosts on the heap, but in that case wait and try again
                if not heap_pair:
                    getLogger().error('Back heap returned no host')

                    sleep(1)

                    continue

                # We can then extract values from the pair, given that it is not None
                wait_time, host = heap_pair

                # If a wait time is specified, wait for that amount
                if wait_time:
                    sleep(wait_time)

                # Look up back queue associated with host
                if host not in self.back_queues:
                    getLogger().error(f'No back queue entry for host {host}')

                    continue

        with ThreadPoolExecutor(max_workers=self.MaxCrawlWorkers) as executor:
            executor.submit(_crawl_)

    def __init__(self, num_front_queues=1):
        # Maintain a list of actively running crawl threads
        self.crawl_threads = list()

        # For certain operations (e.g. the set of seen URLs) a lock is used to avoid conflicts
        self.lock = threading.Lock()

        # Maintain a map of hosts and their parsed robot file
        self.host_robots = dict()

        # Back heap
        self.back_heap = BackHeap()

        # Maintain a map of hosts and their back queues
        self.back_queues = dict()

        # Maintain a set of seen URLs to avoid redundant crawling
        self.seen_urls = set()

        # Maintain a mapping of prioritised front queues
        self.num_front_queues = num_front_queues
        self.front_queues = dict()
        for priority in range(num_front_queues):
            self.front_queues[priority] = FrontQueue()
