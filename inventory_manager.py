class InventoryManager:
    def __init__(self):
        self.stock = {}

    def add_item(self, item_name, quantity):
        self.stock[item_name] = self.stock.get(item_name, 0) + quantity

    def check_stock(self, item_name):
        return self.stock.get(item_name, 0)

    def reduce_stock(self, item_name, quantity):
        if self.check_stock(item_name) >= quantity:
            self.stock[item_name] -= quantity
            return True
        return False


    def low_stock_alert(self, item_name, threshold=10):
        current = self.check_stock(item_name)
        if current < threshold:
            return f"ALERT: {item_name} is low on stock. Only {current} units left"
        return f"{item_name} stock is sufficient"

    def update_stock(self, item_name, quantity):
        self.stock[item_name] = quantity
        return f"Stock updated for {item_name} to {quantity} units"
 
