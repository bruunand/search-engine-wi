import time
from _thread import interrupt_main
from pickle import dump
from threading import Thread

from loguru import logger

from webcrawling.crawler import Crawler

if __name__ == "__main__":
    crawler = Crawler()
    crawler.queue_raw_url('https://twitter.com/search?q=%23dkpol')

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
                dump(crawler.url_contents, open('contents.pkl', 'wb'))
                dump(crawler.url_references, open('references.pkl', 'wb'))
                logger.info('Dump complete')

                interrupt_main()

    thread = Thread(target=log)
    thread.start()

    # Start crawler threads
    crawler.start_crawlers()
