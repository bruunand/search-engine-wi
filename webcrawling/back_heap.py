import heapq
import threading
import time
from logging import getLogger


def _current_time_millis():
    return int(round(time.time() * 1000))


class BackHeap:
    def __init__(self, delay=1000):
        self.lock = threading.Lock()
        self.heap = []
        self.delay = delay
        self.history = set()

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
        if new_host not in self.history:
            self.history.add(new_host)

        with self.lock:
            # If host is already in heap, do not push it
            if new_host in self.get_hosts():
                getLogger().error(f'Attempted to push host {new_host} when already in heap')

                return False

            heapq.heappush(self.heap, (_current_time_millis() + self.delay if delay else 0, new_host))

            return True

    def get_hosts(self):
        return [item[1] for item in self.heap]

    def __contains__(self, item):
        return item in self.get_hosts()
