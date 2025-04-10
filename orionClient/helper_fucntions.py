import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def orderQuantity(order_list):
    order_qty = 0
    for order in order_list:
        # Ensure the order has 'requestQty' and it is a valid number
        if "requestQty" in order and isinstance(order["requestQty"], (int, float)):
            order_qty += order["requestQty"]
        else:
            # Log a warning or handle the case where requestQty is missing or invalid
            logger.warning(f"Order {order['id']} is missing 'requestQty' or it is not a number.")
    return order_qty
