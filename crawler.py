import functools
import heapq
import random
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from queue import Queue, Empty
import time
from urllib.parse import urlparse, urljoin, unquote, urlsplit

from bs4 import BeautifulSoup


def _current_time_millis():
    return int(round(time.time() * 1000))


def log_on_failure(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            getLogger().error(f'Terminating worker exception: {e}')

    return wrapper


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

            next_time, host = heapq.heappop(self.heap)

            # Max is used here to avoid sleeping for a negative duration
            return max(next_time - _current_time_millis(), 0) / 1000, host

    '''
    Add the host to the heap. If delay is specified (typically after the host has been visited) we need to specify
    when the host can be visited again.
    '''

    def push_host(self, new_host, delay=True):
        with self.lock:
            # If host is already in heap, do not push it
            for _, heap_host in self.heap:
                if heap_host == new_host:
                    getLogger().error(f'Attempted to push host {new_host} when already in heap')

                    return

            heapq.heappush(self.heap, (_current_time_millis() + self.DeltaTime if delay else 0, new_host))


class Crawler:
    BaseHeaders = {'User-Agent': 'Kekbot'}
    MaxCrawlWorkers = 2

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

    def move_from_front(self):
        # Randomly select which a front queue
        priority = random.randint(0, self.num_front_queues - 1)
        selected_queue = self.front_queues[priority]

        # Extract URL from queue
        try:
            url = selected_queue.get()
        except Empty:
            return False

        # Get host from URL
        host = urlparse(url).netloc

        # Add to associated back queue
        back_queue = self.back_queues[host]
        if back_queue:
            back_queue.put(url)

    def add_to_frontier(self, url):
        # Add the URL to a random front queue
        priority = random.randint(0, self.num_front_queues - 1)
        self.front_queues[priority].put(url)

    def queue_raw_url(self, url, referer=None):
        illegal_starts = ['mailto:', 'javascript:']
        for start in illegal_starts:
            if url.startswith(start):
                return

        # Normalize URL
        url = self._normalize_url_(url, referer)

        # If we have seen this URL, discard it
        with self.lock:
            if url in self.seen_urls:
                return
            else:
                self.seen_urls.add(url)

        # If host is unseen, create back queue and heap entry
        host = urlparse(url).netloc
        if host not in self.back_queues:
            self.back_queues[host] = Queue()

            # If the host has not been seen before, we can push it to the heap and make it ready immediately
            self.back_heap.push_host(host, delay=False)

        self.add_to_frontier(url)

    @staticmethod
    def _get_hyperlinks_(text):
        hyperlinks = set()
        soup = BeautifulSoup(text, 'lxml')

        for tag in soup.find_all('a', href=True):
            hyperlinks.add(tag['href'])

        return hyperlinks

    def request_url(self, url):
        response = requests.get(url, headers=Crawler.BaseHeaders)

        # If we were redirected, we can also say that this URL has been crawled
        self.seen_urls.add(response.url)
        print(url)
        if response.status_code != 200:
            getLogger().error(f'{url} returned {response.status_code}')

            return None, response.url
        else:
            return response.text, response.url

    '''
    Runs a number of crawlers which will run indefinitely. 
    '''

    def run_crawlers(self):
        # Could principally not be a nested function, but it's nested to discourage calling from main thread
        @log_on_failure
        def _crawl_():
            while True:
                # Get next host to crawl and time we need to wait
                heap_pair = self.back_heap.pop_host()

                # It should not occur that there are no hosts on the heap, but in that case wait and try again
                if not heap_pair:
                    getLogger().error('Back heap returned no host')

                    time.sleep(1)

                    continue

                # We can then extract values from the pair, given that it is not None
                wait_time, host = heap_pair

                # If a wait time is specified, wait for that amount
                if wait_time:
                    time.sleep(wait_time)

                # Look up back queue associated with host
                if host not in self.back_queues:
                    getLogger().error(f'No back queue entry for host {host}')

                    continue

                # Pull URL to visit from back queue, continue until the back queue is non-empty
                back_queue = self.back_queues[host]
                while back_queue.empty():
                    self.move_from_front()

                # Pull URL from non-empty back queue
                url = back_queue.get()

                try:
                    # Get contents of extracted URL
                    text, url = self.request_url(url)
                    if not text or not url:
                        continue

                    # Get hyperlink from contents
                    hyperlinks = self._get_hyperlinks_(text)

                    # Add hyperlinks to queue
                    for hyperlink in hyperlinks:
                        self.queue_raw_url(hyperlink, referer=url)
                except Exception as e:
                    getLogger().error(f'Worker exception: {e}')
                finally:
                    # Even an exception occurs, push back the host to the heap
                    self.back_heap.push_host(host, delay=True)

        with ThreadPoolExecutor(max_workers=self.MaxCrawlWorkers) as executor:
            for i in range(self.MaxCrawlWorkers):
                executor.submit(_crawl_)

    def __init__(self, num_front_queues=1):
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
            self.front_queues[priority] = Queue()


'''
Cut corners:
- I have not implemented prioritization in front queues. It uses a random system which is really no better than having
one large queue.
- I do not differentiate between www.[host] and [host]. In practice they can result in different IP addresses.
'''
