import time
from threading import Thread

from indexing.indexer import Indexer
from querying.query import Query
from webcrawling.crawler import Crawler

if __name__ == "__main__":
    crawler = Crawler()

    # Add seed URLs
    #crawler.queue_raw_url("http://reddit.com")
    crawler.queue_raw_url('http://www.aau.dk')

    # Start logger thread
    def logger():
        while True:
            print(f'{len(crawler.seen_urls)} seen URLs, {len(crawler.back_heap.get_hosts())} hosts, {len(crawler.back_queues)} back queues')
            print(f'Unindexed: {crawler.unindexed.qsize()}')
            print(f'Requests made: {crawler.num_requests}')
            time.sleep(5)

    thread = Thread(target=logger)
    thread.start()

    # Run indexer thread
    indexer = Indexer(crawler.unindexed)
    indexer.start_indexer()

    # Start crawler threads
    crawler.start_crawlers()

    # Run queries
    while True:
        query = Query(indexer, "matias OR matias")

        for id in query.get_matches():
            print(indexer.url_vocabulary.get(id))

        time.sleep(1)
