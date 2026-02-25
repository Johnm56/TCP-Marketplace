# inventory.py
import threading

class Inventory:
    def __init__(self, amount):
        self.amount = amount
        self.lock = threading.Lock()  # ensures thread-safe stock updates

    def buy(self, qty):
        with self.lock: # lock prevents race conditions
            if qty <= self.amount: 
                self.amount -= qty # reduce available stock
                return True 
            return False # not enough stock

    def get_amount(self):
        with self.lock:
            return self.amount