import functools
import random
import threading
import time
from logging import getLogger
from queue import Queue, Empty
from urllib.parse import urlparse, urljoin, unquote, urlsplit

import requests
from bs4 import BeautifulSoup

from webcrawling.back_heap import BackHeap
from webcrawling.parser.robots_parser import RobotsParser


def log_on_failure(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            getLogger().error(f'Terminating worker exception: {e}')

    return wrapper


class Crawler:
    UserAgent = 'Kekbot'
    BaseHeaders = {'User-Agent': UserAgent}
    WorkerThreads = 10

    @staticmethod
    def _normalize_url(url, referer=None):
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

    def queue_raw_url(self, url):
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

    def get_hyperlinks(self, soup, referer):
        hyperlinks = set()
        illegal_starts = {'mailto:', 'javascript:', '#'}

        for tag in soup.find_all('a', href=True):
            href = tag['href']

            for start in illegal_starts:
                if href.startswith(start):
                    break
            else:
                hyperlinks.add(self._normalize_url(href, referer))

        return hyperlinks

    def get_robots_parser(self, host):
        if host in self.host_robots:
            return self.host_robots[host]

        response, _ = self.request_url(f'http://{host}/robots.txt')
        if response:
            self.host_robots[host] = RobotsParser(robot_text=response)
        else:
            # If robots could not be accessed, an empty parser is used which allows anything
            self.host_robots[host] = RobotsParser()

        return self.host_robots[host]

    def request_url(self, url):
        response = requests.get(url, headers=Crawler.BaseHeaders, timeout=5)

        # If we were redirected, we can also say that this URL has been crawled
        self.seen_urls.add(response.url)

        if response.status_code != 200:
            # getLogger().error(f'{url} returned {response.status_code}')

            return None, response.url
        else:
            return response.text, response.url

    """ Runs a number of crawlers which will run indefinitely. """

    def start_crawlers(self):
        self.crawling = True

        # Could principally not be a nested function, but it's nested to discourage calling from main thread
        @log_on_failure
        def _crawl():
            while self.crawling:
                # Get next host to crawl and time we need to wait
                heap_pair = self.back_heap.pop_host()

                # It should not occur that there are no hosts on the heap, but in that case wait and try again
                if not heap_pair:
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
                    # Check if we are allowed to visit the URL
                    url_path = urlparse(url).path
                    if not self.get_robots_parser(host).can_access(url_path, user_agent=self.UserAgent):
                        # getLogger().error(f'Not allowed to visit {url}')

                        continue

                    # Increment request counter
                    self.num_requests += 1

                    # Get contents of extracted URL
                    text, url = self.request_url(url)
                    if not text or not url:
                        getLogger().error(f'Failed to get {url}')

                        continue

                    # Parse with BS4
                    soup = BeautifulSoup(text, 'lxml')
                    if not soup:
                        getLogger().error(f'Could not parse {url}')

                        continue

                    # Get hyperlink from contents
                    hyperlinks = self.get_hyperlinks(soup, url)

                    # Add hyperlinks to queue
                    for hyperlink in hyperlinks:
                        self.queue_raw_url(hyperlink)

                    # Set outgoing links for current URL
                    self.url_references[url] = hyperlinks

                    # Remove irrelevant tags
                    for tag in soup(["script", "style"]):
                        tag.extract()

                    self.unindexed.put((url, soup.text))
                except Exception as e:
                    getLogger().error(f'Worker exception: {e}')
                finally:
                    # Even an exception occurs, push back the host to the heap
                    self.back_heap.push_host(host, delay=True)

        for i in range(self.WorkerThreads):
            thread = threading.Thread(target=_crawl)
            thread.start()

    def stop_crawlers(self):
        self.crawling = False

    def __init__(self, num_front_queues=1):
        self.crawling = False

        # Maintain a dictionary from URLs to their referenced URLs
        self.url_references = dict()

        # Maintain a counter of requests made
        self.num_requests = 0

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

        # Maintains a queue of unindexed text
        self.unindexed = Queue()

        # Maintain a mapping of prioritised front queues
        self.num_front_queues = num_front_queues
        self.front_queues = dict()
        for priority in range(num_front_queues):
            self.front_queues[priority] = Queue()


'''
Cut corners:
- I have not implemented prioritization in front queues. It uses a random system which is really no better than having
one large queue.
- I do not differentiate between www.[host] and [host]. In practice they can result in different IP addresses and
different robot files, so perhaps it's not really an issue.
'''
