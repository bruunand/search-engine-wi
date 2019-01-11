import time
from pickle import dump
from threading import Thread

from loguru import logger

from webcrawling.crawler import Crawler

if __name__ == "__main__":
    crawler = Crawler()

    # Add seed URLs
    crawler.queue_raw_url('http://aau.dk')
    crawler.queue_raw_url('https://www.cs.aau.dk/')
    crawler.queue_raw_url('http://anderslangballe.dk')
    crawler.queue_raw_url('http://tv2.dk')

    # Start logger thread
    def log():
        while True:
            logger.info(
                f'{len(crawler.seen_urls)} seen URLs, {len(crawler.back_heap.get_hosts())} waiting hosts, {len(crawler.back_queues)} back queues')
            logger.info(f'Requests made: {crawler.num_requests}')
            logger.info(f'Contents: {len(crawler.url_contents)}')
            time.sleep(5)

            # If a certain content length has been reached, terminate
            if len(crawler.url_contents) > 3000:
                logger.info('Dumping contents and references...')
                dump(crawler.url_contents, open('contents.p', 'wb'))
                dump(crawler.url_references, open('references.p', 'wb'))
                logger.info('Dump complete')

                return


    thread = Thread(target=log)
    thread.start()

    # Start crawler threads
    crawler.start_crawlers()

