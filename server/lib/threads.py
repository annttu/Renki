# encoding: utf-8

"""
Renki threads
"""

from lib.exceptions import Stopped
import threading
import time


server_threads = []

class RenkiThread(threading.Thread):
    def __init__(self):
        self._stopped = False
        threading.Thread.__init__(self)
        server_threads.append(self)

    def stop(self):
        self._stopped = True
        self.post_stop()

    def post_stop(self):
        pass

    def is_stopped(self):
        return self._stopped

    def safe_wait(self, duration):
        begin = time.time()
        end = begin + duration
        while time.time() < end:
            sleep(0.1)
            if self._stopped:
                raise Stopped("Thread stopped")
