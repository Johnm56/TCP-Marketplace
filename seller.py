# seller.py
import socket
import threading
from protocol import ENCODING, encode, MAX_SELL_TIME
from seller_node import SellerNode

class SellerServer:
    def __init__(self, ip, port):
        self.ip = ip # Seller server network address
        self.port = port
        self.clients = [] # List of connected buyers (TCP sockets)
        self.next_id = 1
        self.buyer_ids = {}   # Manage automatic IDs
        self.seller = SellerNode(event_callback=self.handle_seller_event) # Logic layer for item rotation, timers, and stock

    def send_msg(self, conn, message):
        try:
            conn.sendall(message.encode(ENCODING)) #Sends a message to one connected buyer
        except:
            pass

    def broadcast(self, message):  #Sends a message to all connected buyers
        for c in list(self.clients):
            self.send_msg(c, message)

    def handle_seller_event(self, event_type, item, value): #Receive events from SellerNode and forward to buyers
        if event_type == "NEWITEM":
            self.broadcast(encode("NEWITEM", item, value))
        elif event_type == "TIMELEFT":
            self.broadcast(encode("TIMELEFT", item, value))
        elif event_type == "TIMEEXPIRED":
            self.broadcast(encode("TIMEEXPIRED", item))
        elif event_type == "MARKETCLOSED":
            self.broadcast(encode("MARKETCLOSED"))
            print("[Seller] Broadcasted MARKET CLOSED to all buyers.")

    def handle_client(self, conn): #Handle one buyer connection
        file = conn.makefile("r")

        while True:
            try:
                line = file.readline()
                if not line:
                    break
            except:
                break

            parts = line.strip().split("|")
            if not parts:
                continue

            cmd = parts[0]

            if cmd == "LIST": # Handle LIST request
                if self.seller.current_item is None or self.seller.inventory is None:
                    self.send_msg(conn, encode("MARKETCLOSED"))
                else:
                    msg = encode("ITEM",
                                 self.seller.current_item,
                                 self.seller.inventory.get_amount())
                    self.send_msg(conn, msg)
                    
            elif cmd == "BUY": # Handle BUY request
                # simple input validation
                if len(parts) != 4:
                    self.send_msg(conn, encode("ERROR", "Invalid BUY format"))
                    continue

                _, buyer_id, item, amount_str = parts

                if not amount_str.isdigit():
                    self.send_msg(conn, encode("ERROR", "Amount must be a number"))
                    continue

                amount = int(amount_str)
 
                if item != self.seller.current_item:  # Wrong item check
                    self.send_msg(conn, encode("WRONGITEM"))
                    continue

                ok, left = self.seller.process_purchase(buyer_id, amount)

                if ok:
                    confirmation_text = f"buyer {buyer_id} bought {amount} of {item} from seller" # Purchase confirmation to the buyer
                    self.broadcast(encode("UPDATE", item, left)) # Broadcast new stock
                    self.send_msg(conn, encode("CONFIRM", confirmation_text))  
                else:
                    self.send_msg(conn, encode("FAILED"))

        # clean close
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except:
            pass
        conn.close()

    def start(self):
        # Start first item
        self.seller.start_selling_new_item()

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.ip, self.port))
        server.listen(5)
        print(f"[Seller] Running on {self.ip}:{self.port}")

        while True:
            conn, addr = server.accept()
            self.clients.append(conn)
            assigned_id = self.next_id
            self.next_id += 1
            self.buyer_ids[conn] = assigned_id
            # send ID to buyer
            self.send_msg(conn, encode("ASSIGNID", assigned_id))
            print(f"[Seller] Buyer connected: {addr}, assigned ID = {assigned_id}")

            # When a new buyer joins:
            if self.seller.current_item is None:
                # market already closed
                self.send_msg(conn, encode("MARKETCLOSED"))
            else:
                # send them current item + full 60-second timer
                self.send_msg(conn, encode("NEWITEM",
                                           self.seller.current_item,
                                           self.seller.inventory.get_amount()))
                self.send_msg(conn, encode("TIMELEFT",
                                           self.seller.current_item,
                                           MAX_SELL_TIME))

            threading.Thread(target=self.handle_client,
                             args=(conn,),
                             daemon=True).start()


if __name__ == "__main__":
    SellerServer("127.0.0.1", 6010).start()