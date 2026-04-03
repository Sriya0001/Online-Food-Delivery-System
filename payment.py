class PaymentService:
    def __init__(self):
        self.transactions = []

    def process_payment(self, order_id, amount, method):
        transaction = {
            "order_id": order_id,
            "amount": amount,
            "method": method,
            "status": "Success"
        }
        self.transactions.append(transaction)
        return transaction

    def get_transaction(self, order_id):
        for t in self.transactions:
            if t["order_id"] == order_id:
                return t
        return None

    def refund_payment(self, order_id):
        for t in self.transactions:
            if t["order_id"] == order_id:
                t["status"] = "Refunded"
                return f"Order {order_id} refunded successfully"
        return "Transaction not found"

    def get_payment_summary(self):
        total = sum(t["amount"] for t in self.transactions)
        return f"Total transactions: {len(self.transactions)}, Total amount: {total}"