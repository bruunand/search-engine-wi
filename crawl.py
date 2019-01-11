import sys
import time
from threading import Thread

from webcrawling.crawler import Crawler
from pickle import dump

if __name__ == "__main__":
    crawler = Crawler()

    # Add seed URLs
    crawler.queue_raw_url('http://aau.dk')
    crawler.queue_raw_url('http://anderslangballe.dk')
    crawler.queue_raw_url('https://www.reddit.com/r/worldnews')
    crawler.queue_raw_url('https://twitter.com/search?q=%23dkpol')
    crawler.queue_raw_url('https://edition.cnn.com/')

    # Start logger thread
    def logger():
        while True:
            print(
                f'{len(crawler.seen_urls)} seen URLs, {len(crawler.back_heap.get_hosts())} waiting hosts, {len(crawler.back_queues)} back queues')
            print(f'Requests made: {crawler.num_requests}')
            print(f'References: {len(crawler.url_references)}')
            print(f'Contents: {len(crawler.url_contents)}')
            time.sleep(5)

            # If a certain content length has been reached, terminate
            if len(crawler.url_contents) > 5000:
                print('Dumping contents and references...')
                dump(crawler.url_contents, open('contents.p', 'wb'))
                dump(crawler.url_references, open('references.p', 'wb'))
                print('Dump complete')


    thread = Thread(target=logger)
    thread.start()

    # Start crawler threads
    crawler.start_crawlers()

