import time
from threading import Thread

from crawler import Crawler

if __name__ == "__main__":
    crawler = Crawler()

    # Add seed URLs
    crawler.queue_raw_url("http://eb.dk")
    crawler.queue_raw_url('http://tv2.dk')

    # Start logger thread
    def logger():
        while True:
            print(f'{len(crawler.seen_urls)} seen URLs, {crawler.back_heap.get_hosts()}')

            time.sleep(5)

    thread = Thread(target=logger)
    thread.start()

    # Start crawler threads
    crawler.run_crawlers()
