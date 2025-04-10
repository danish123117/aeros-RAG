from flask import Flask, render_template, request, jsonify
import requests
from waitress import serve
import os
from datetime import datetime, timezone
import requests
import json
from datetime import datetime, timezone
import logging
from orionClient.orion_client import *



logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
app = Flask(__name__)

global in_process_list
in_process_list = []
global lea_order
lea_order = None


ORION_LD_URL = os.getenv("ORION_LD_URL", "localhost")
ORION_LD_PORT = os.getenv("ORION_LD_PORT", 1026)
CONTEXT_URL = os.getenv("CONTEXT_URL", "context")
CONTEXT_PORT = os.getenv("CONTEXT_PORT", 5051)


auth_token = None

def orderQuantity(order_list):
    order_qty = 0
    for order in order_list:
        qty = order.get("orderQuantity")
        if isinstance(qty, (int, float)):
            order_qty += qty
        else:
            logger.warning(f"Order {order.get('id')} is missing 'requestQty' or it is not a number.")
            continue
    return order_qty

def complete_production(data): 
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-2]
    
    # Initialize completedOrderList if it doesn't exist
    if "completedOrderList" not in data:
        data["completedOrderList"] = {"type": "Property", "value": []}
    elif not isinstance(data["completedOrderList"], dict):
        data["completedOrderList"] = {"type": "Property", "value": []}
    elif "value" not in data["completedOrderList"]:
        data["completedOrderList"]["value"] = [] 
    # Get processing orders
    processing_orders = data.get("processingOrderList", {}).get("value", [])   
    # Add timestamp and move to completed orders
    for order in processing_orders:
        if not isinstance(order, list):
            order = [order]
        order_copy = order.copy()
        order_copy.append(timestamp)  # Add completion timestamp
        data["completedOrderList"]["value"].append(order_copy)
    data["processingOrderList"]["value"] = [] 
    return data

def get_current_order_number():
    global lea_order
    response = requests.get(WMS_ORDER_INFO_URL, auth=(WMS_USERNAME, WMS_PASSWORD))
    if response.status_code == 200:
        orders = response.json()
        for order in orders:
            if order['status'] !='COMPLETED' and order['status'] !="CANCELLED" and order["id"]>=258204:
                lea_order= order["orderNumber"]  
    if lea_order is None:
        logger.warning("LEA order is not set.")
        return None
    else:
        return lea_order
    
def track_order_status(order_number):
    url = f"{WMS_ORDER_INFO_URL}?orderNumber={order_number}"
    response = requests.get(url, auth=(WMS_USERNAME, WMS_PASSWORD))
    if response.status_code == 200:
        order_info = response.json()
        if order_info and isinstance(order_info, list):
            return order_info[0].get("status")
        else:
            logger.warning(f"Order {order_number} not found or invalid response format.")
            return None
    else:
        logger.error(f"Failed to fetch order status: {response.text}")
        return None

# Function to post order to factory
def post_order_to_factory(order_qty):
    payload = json.dumps([
        {
            "item": {"itemNumber": "VALVOLA"},
            "bom": {"bomId": "DEMO"},
            "requestQty": order_qty,
        }
    ])
    response = requests.post(WMS_POST_URL, data=payload, auth=(WMS_USERNAME, WMS_PASSWORD))
    order_number = get_current_order_number()
    if response.status_code == 200:
        logger.info(f"Order {order_number} posted successfully.")
        return order_number
    else:
        logger.error(f"Failed to post order: {response.text}")
        return None

@app.route("/")
def home():
    incomplete_orders, processing_orders, completed_orders = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    return render_template("index.html", incomplete_orders=incomplete_orders, processing_orders=processing_orders, completed_orders=completed_orders)

@app.route("/start_production", methods=["POST"])
def start_production():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "Baseline")
    mode ="Base"
    if mode == "Baseline": 
        n=2
    else: 
        n=6

    incomplete_orders, _, _ = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    print(f"Number of incomplete orders: {len(incomplete_orders)}")
    if len(incomplete_orders) != 0:
        for i in range(n):
            if orderQuantity(incomplete_orders[:i+1]) <= n: 
                print(f"Processing order {i+1} with quantity {orderQuantity(incomplete_orders[:i+1])}")
                continue
            else:
                break
        in_process_list = incomplete_orders[:i]
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-2]
        response_patch =update_processing_order_list(in_process_list, ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT,timestamp)
        response_factory = post_order_to_factory(orderQuantity(in_process_list))
        if response_patch and response_factory:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False})
        # if response_patch:
        #     return jsonify({"success": True})
        # else:
        #     return jsonify({"success": False})
    else:
        return jsonify({"Status": "No orders to process"})



@app.route("/complete_production", methods=["POST"])
def complete_production():
    global lea_order
    _, in_process_list, _ = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    if in_process_list:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-2]
        response = update_complete_order_list(in_process_list, ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT,timestamp)
        if response:
            lea_order = None
            return jsonify({"success": True})
        else:
            return jsonify({"success": False})
    else:
        return jsonify({"Status": "No orders to complete"})
  

@app.route('/get_orders', methods=['GET'])# Done
def get_order():
    incomplete_orders, processing_orders, comleted_orders = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    return jsonify({"incomplete_orders": incomplete_orders, "processing_orders": processing_orders, "completed_orders": comleted_orders})

@app.route('/get_completed_orders', methods=['GET']) # Done
def get_order_info():
    _, _, comleted_orders = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    return jsonify({"completed_orders": comleted_orders})

@app.route('/history', methods=['GET'])#
def history():
    _, _, comleted_orders = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    return render_template("history.html", completed_orders=comleted_orders)


@app.route('/current_order_status', methods=['GET'])
def lea_status():
    global lea_order
    order_number = lea_order
    if order_number is None:
        order_number = get_current_order_number()
    if order_number:
        status = track_order_status(order_number)
        if status:
            return jsonify({"status": status})
        else:
            return jsonify({"error": "Failed to fetch order status"}), 500
    else:
        return jsonify({"error": "No current LEA order number found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3040,debug=True)
    #serve(app, host="0.0.0.0", port=3040)