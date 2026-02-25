ENCODING = "utf-8"
BUFFER = 1024
ITEMS = ["flower", "sugar", "potato", "oil"] # All items the marketplace can ever sell
MAX_SELL_TIME = 60 # Timer length for each item

def encode(*parts):
    return "|".join(str(p) for p in parts) + "\n" # Converts message fields into a pipe-separated string with newline

def decode(message):
    return message.split("|") # Splits a message into fields