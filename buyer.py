# buyer.py
import socket
import sys
import threading
from protocol import ENCODING, encode
from buyer_node import BuyerNode

class BuyerClient:
    def __init__(self, ip, port, buyer_id):
        self.ip = ip     # seller address
        self.port = port # seller port
        self.node = BuyerNode(buyer_id) # store buyer ID
        self.sock = None
        self.show_prompt_after_signal = True # controls printing input prompt

    def print_prompt(self):
        sys.stdout.write("Enter command (list/buy/exit): ") # prints input prompt without newline
        sys.stdout.flush()

    def listen_server(self):
        #Background thread: prints any messages from the seller
        file = self.sock.makefile("r")
        while True:
            line = file.readline()
            if not line:
                break

            msg = line.strip()
            cmd = msg.split("|")[0]
            if cmd == "ASSIGNID": # seller assigns automatic ID
                self.node.id = msg.split("|")[1]
                print(f"\n[INFO] Assigned Buyer ID = {self.node.id}")
                continue
        
            print(f"\n[SIGNAL] {msg}")  # show any server signal
            
            if cmd in ("CONFIRM", "UPDATE"): # hide prompt for confirm/update
                self.show_prompt_after_signal = False
            else:
                self.show_prompt_after_signal = True

    def start(self):
        self.sock = socket.socket()  # connect to seller
        self.sock.connect((self.ip, self.port))
        print("[Buyer] Connected to seller")

        # start listener thread
        threading.Thread(target=self.listen_server, daemon=True).start()

        while True:
            if self.show_prompt_after_signal:
                print("Enter command (list/buy/exit): ", end="")

            cmd = input().strip()
            self.show_prompt_after_signal = True # Reset

            if cmd == "list":
                self.sock.sendall(encode("LIST").encode(ENCODING)) # request current item

            elif cmd == "buy": # gather buy details
                item = input("Item: ").strip()
                amount = input("Amount: ").strip()
                self.sock.sendall(self.node.make_buy_message(item, amount).encode(ENCODING))

            elif cmd == "exit": # close connection
                self.sock.close()
                break


if __name__ == "__main__":
    buyer_id = None  # ID assigned automatically by seller
    BuyerClient("127.0.0.1", 6010, buyer_id).start()