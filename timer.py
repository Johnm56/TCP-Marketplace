# timer.py
import threading
import time

class SaleTimer(threading.Thread):
    def __init__(self, duration, callback): 
        super().__init__()
        self.duration = duration # Number of seconds the item should be sold for
        self.callback = callback
        self.running = True 

    def run(self):
        time.sleep(self.duration)
        if self.running:
            self.callback() # Timer reached zero

    def stop(self):
        self.running = False