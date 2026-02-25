# buyer_node.py
# This class represents the local state of a buyer
from protocol import encode
# Build a BUY request message in the correct protocol format
class BuyerNode:
    def __init__(self, buyer_id):
        self.id = buyer_id

    def make_buy_message(self, item, amount):
        return encode("BUY", self.id, item, amount)