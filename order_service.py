 
class OrderService:
    def __init__(self):
        self.orders = []

    def place_order(self, customer_id, items):
        order = {
            "order_id": len(self.orders) + 1,
            "customer_id": customer_id,
            "items": items,
            "status": "Placed"
        }
        self.orders.append(order)
        return order

    def get_order_status(self, order_id):
        for order in self.orders:
            if order["order_id"] == order_id:
                return order["status"]
        return "Order not found"
    

    def cancel_order(self, order_id):
        for order in self.orders:
            if order["order_id"] == order_id:
                order["status"] = "Cancelled"
                return f"Order {order_id} cancelled successfully"
        return "Order not found"

    def update_order_status(self, order_id, new_status):
        valid_statuses = ["Placed", "Preparing", "Out for Delivery", "Delivered"]
        if new_status not in valid_statuses:
            return "Invalid status"
        for order in self.orders:
            if order["order_id"] == order_id:
                order["status"] = new_status
                return f"Order {order_id} updated to {new_status}"
        return "Order not found"