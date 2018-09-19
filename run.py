import time

from crawler import Crawler

if __name__ == "__main__":
    crawler = Crawler()
    crawler.queue_raw_url("http://eb.dk")
    crawler.run_crawlers()

    while True:
        time.sleep(10)
