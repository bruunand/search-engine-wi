import functools
import random
import threading
import time
from logging import getLogger
from queue import Queue, Empty
from urllib.parse import urlparse, urljoin, unquote, urlsplit

import requests
from bs4 import BeautifulSoup
from loguru import logger
from tld import get_tld

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
    UserAgent = 'Wibot'
    BaseHeaders = {'User-Agent': UserAgent}

    def normalize_url(self, url, referer=None):
        """ Normalizes URL, expands relative URLs to absolute ones """
        # Expand relative links
        if referer:
            url = urljoin(referer, url)

        # Converts protocol and host to lower case
        url = urlsplit(url).geturl()

        # Decode percent-encoded octets of unreserved characters
        url = unquote(url)

        # Remove anchor scrolling
        if '#' in url:
            url = url.split('#')[0]

        # Remove trailing slash if any
        url = url.rstrip('/')

        return url

    def pick_from_front(self):
        # Randomly select which a front queue
        priority = random.randint(0, self.num_front_queues - 1)
        selected_queue = self.front_queues[priority]

        # Extract URL from queue
        try:
            url = selected_queue.get()
        except Empty:
            return False

        return url

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

        parsed_url = urlparse(url)
        host = parsed_url.netloc

        # Check if we can visit this URL
        if not self.get_robots_parser(host).can_access(parsed_url.path, user_agent=self.UserAgent):
            return

        # For initial hosts, create a back queue and heap entry for them
        with self.lock:
            if len(self.back_queues) < self.num_back_queues and host not in self.back_heap.history:
                queue = Queue()

                # Our seeds get "special treatment" by instantly being put in a back queue
                queue.put(url)
                self.host_queue_map[host] = queue
                self.back_queues.add(queue)
                self.back_heap.push_host(host, delay=True)
            else:
                self.add_to_frontier(url)

    def get_hyperlinks(self, soup, referer):
        hyperlinks = dict()
        illegal_starts = {'mailto:', 'javascript:', '#', 'tel:'}

        for tag in soup.find_all('a', href=True):
            href = tag['href']

            for start in illegal_starts:
                if href.startswith(start):
                    break
            else:
                hyperlinks[self.normalize_url(href, referer)] = tag.text

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
            # Check if content is text/html
            content_type = response.headers.get('Content-Type', None)
            if not content_type or 'text' not in content_type:
                return None, response.url

            return response.text, response.url

    def add_contents(self, url, contents):
        contents = contents.strip()
        if not contents:
            return

        self.url_contents[url] = f'{contents} {self.url_contents.get(url, "")}'.strip()

    def fetch_url(self, url):
        """ Fetches a URL, performs parsing of it, passes to indexer and saves outgoing links """
        try:
            self.num_requests += 1

            # Get contents of extracted URL
            text, url = self.request_url(url)
            if not text or not url:
                getLogger().error(f'Failed to get {url}')

                return False

            # Parse with BS4
            soup = BeautifulSoup(text, 'lxml')
            if not soup:
                getLogger().error(f'Could not parse {url}')

                return False

            # Get hyperlink from contents
            hyperlinks = self.get_hyperlinks(soup, url)

            # Set outgoing links for current URL
            # Update contents of referenced URLs to include anchor text
            references = set()
            for hyperlink, anchor_text in hyperlinks.items():
                if hyperlink in self.url_contents:
                    self.add_contents(hyperlink, anchor_text)

                if hyperlink != url:
                    references.add(hyperlink)

            # Only add references that are not referenced by the same host
            self.url_references[url] = references

            # Add hyperlinks to URL frontier
            for hyperlink in hyperlinks:
                self.queue_raw_url(hyperlink)

            # Remove irrelevant tags
            for tag in soup(["script", "style"]):
                tag.extract()

            # Add to dictionary of URL contents
            self.add_contents(url, soup.text)
        except Exception as e:
            getLogger().error(f'Worker exception: {e}')
            return False

        return True

    def start_crawlers(self):
        """ Runs a number of crawlers which will run indefinitely. """
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
                back_queue = self.host_queue_map[host]

                # Pull URL from back queue and fetch its contents
                self.fetch_url(back_queue.get())

                # Refill the back queue if necessary
                while back_queue.empty():
                    # Pull a URl from a prioritised front queue
                    url = self.pick_from_front()
                    new_host = urlparse(url).netloc

                    # Check if the new host has an existing back queue
                    with self.lock:
                        existing = self.host_queue_map.get(new_host)

                        if existing:
                            # The URL selected from a front queue already has a queue
                            existing.put(url)
                        else:
                            # The current back queue is transferred to the new host
                            host = new_host
                            self.host_queue_map[host] = back_queue
                            back_queue.put(url)

                # Add entry to heap
                self.back_heap.push_host(host, delay=True)

        # Start the designated number of threads
        for _ in range(self.threads):
            thread = threading.Thread(target=_crawl)
            thread.start()

    def stop_crawlers(self):
        self.crawling = False

    def __init__(self, threads=100, num_front_queues=1):
        self.crawling = False
        self.threads = threads

        # Maintains a dictionary from URLs to their contents
        self.url_contents = dict()

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

        # Maintain a set of seen URLs to avoid redundant crawling
        self.seen_urls = set()

        # Maintain a mapping of prioritised front queues
        self.num_front_queues = num_front_queues
        self.front_queues = dict()
        for priority in range(num_front_queues):
            self.front_queues[priority] = Queue()

        # Maintain a mapping from hosts to their back queue
        self.host_queue_map = dict()

        # Maintain a set of back queues
        self.back_queues = set()
        self.num_back_queues = threads * 3
