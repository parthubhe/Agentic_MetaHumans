import os

MED_STOCK_FILE = r"./NA_Utils/medication_stock.txt"

def load_medication_stock():
    """Loads medication stock from file."""
    stock = {}
    if os.path.exists(MED_STOCK_FILE):
        with open(MED_STOCK_FILE, 'r') as f:
            for line in f:
                name, quantity = line.strip().split(',')
                stock[name] = int(quantity)
    return stock

def save_medication_stock(stock):
    """Saves medication stock to file."""
    with open(MED_STOCK_FILE, 'w') as f:
        for name, quantity in stock.items():
            f.write(f"{name},{quantity}\n")

def add_medication_stock(stock, name, quantity):
    """Adds medication stock."""
    if name in stock:
        stock[name] += quantity
    else:
        stock[name] = quantity
    save_medication_stock(stock)
    return stock

def reduce_medication_stock(stock, name, quantity):
    """Reduces medication stock."""
    if name in stock:
        if stock[name] >= quantity:
            stock[name] -= quantity
            save_medication_stock(stock)
            return stock, None # No error
        else:
            return stock, "Error: Not enough stock to reduce." # Error message
    else:
        return stock, "Error: Medication not found in stock." # Error message