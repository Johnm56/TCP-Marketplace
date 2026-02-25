# seller_node.py
import random
from inventory import Inventory
from timer import SaleTimer
from protocol import ITEMS, MAX_SELL_TIME

class SellerNode:
    def __init__(self, seller_id="SELLER", event_callback=None):
        self.seller_id = seller_id # Identity of seller
        self.current_item = None # Current item details
        self.inventory = None
        self.timer = None # Timer used to expire item after 60 seconds
        self.sold_out_items = set()     # items that can never be sold again
        self.event_callback = event_callback # Callback to SellerServer for sending network notifications
        self.inventories = {item: Inventory(amount=5) for item in ITEMS} # Persistent inventory for each item

    def _start_timer(self):
        # stop previous timer (if any) and start a fresh one
        if self.timer:
            self.timer.stop()
        self.timer = SaleTimer(MAX_SELL_TIME, self.time_expired_switch)
        self.timer.start()

    def start_selling_new_item(self):
        #Pick a new item (not sold out), reset inventory & timer
        available_items = [
            i for i in ITEMS
            if i not in self.sold_out_items and self.inventories[i].get_amount() > 0
        ]

        if not available_items:
            print("[SellerNode] ALL ITEMS SOLD OUT — Marketplace closing.")
            self.current_item = None
            self.inventory = None

            # tell server so it can broadcast MARKETCLOSED
            if self.event_callback:
                self.event_callback("MARKETCLOSED", None, 0)
            return False

        if self.current_item in available_items and len(available_items) > 1:
            available_items = [i for i in available_items if i != self.current_item] # Avoid repeating same item back-to-back
        self.current_item = random.choice(available_items)
        self.inventory = self.inventories[self.current_item]
        print(f"[SellerNode] Now selling: {self.current_item} (5 units)")

        # start timer for this item
        if self.timer:
            self.timer.stop()

        self.timer = SaleTimer(MAX_SELL_TIME, self.time_expired_switch)
        self.timer.start()

        # tell buyers new item + time left
        if self.event_callback:
            self.event_callback("NEWITEM", self.current_item, self.inventory.get_amount())
            self.event_callback("TIMELEFT", self.current_item, MAX_SELL_TIME)

        return True

    def time_expired_switch(self):
        #Called by SaleTimer when 60 seconds are up
        print("[SellerNode] Time expired -> Switching item")
        if self.event_callback:
            self.event_callback("TIMEEXPIRED", self.current_item, 0)
        self.start_selling_new_item()

    def sold_out_switch(self):
        #Called when current item stock reaches 0 because of purchases
        print(f"[SellerNode] SOLD OUT: {self.current_item} cannot be sold again.")
        self.sold_out_items.add(self.current_item)
        # move on to the next item (or close market if none left)
        self.start_selling_new_item()

    def process_purchase(self, buyer_id, amount):
        #Try to buy 'amount' of current_item. Returns (success, left)
        if not self.inventory or not self.current_item:
            return False, 0

        success = self.inventory.buy(amount)
        left = self.inventory.get_amount()

        if success:
            # required assignment print
            print(f"buyer {buyer_id} bought {amount} of {self.current_item} from {self.seller_id}")
            ## Switch item immediately if stock hits zero
            if left == 0:
                if self.timer:
                    self.timer.stop()
                self.sold_out_switch()

        return success, left