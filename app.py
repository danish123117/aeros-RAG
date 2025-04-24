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
#################################################################################################
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

def Mlprocessing(input_val):
    Model = None
    #TODO create the MLmodel
    return Model(input_val)

def choose_top_n(incomplete_order_list, n):
    if len(incomplete_order_list) != 0:
        for i in range(n):
            if orderQuantity(incomplete_order_list[:i+1]) <= n: 
                print(f"Processing order {i+1} with quantity {orderQuantity(incomplete_order_list[:i+1])}")
                continue
            else:
                break
        in_process_list = incomplete_order_list[:i]
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-2]
        response_patch = update_outsource_processing_order_list(in_process_list, ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT,timestamp)
        if response_patch:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False})
    else:
        return jsonify({"Status": "No orders to process"})

@app.route("/complete_production", methods=["POST"])
def complete_production():
    n = 3
    incomplete_orders_list, in_process_list, complete_orders_list = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    queue_size, process_stat =  len(incomplete_orders_list), 1 if len(in_process_list) > 0 else 0 # first input, and thrid input 
    if process_stat:
        start_time = in_process_list[0]["productionStartTime"]
        quantity = orderQuantity(in_process_list) 
        time_to_finish = quantity*7.5 + 3 -(datetime.now() - start_time) # the time difference should be in minutes
        #TODO complete the convertion of datetime.now() - start_time
        #TODO average of creationTime in all three list for top n ex 10.
        average_inter_arrival = None

        outsourcing_action = Mlprocessing(start_time, quantity, time_to_finish, average_inter_arrival)

        if outsourcing_action:
            choose_top_n(incomplete_orders_list, n)
    


if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=3040,debug=True) 
    serve(app)