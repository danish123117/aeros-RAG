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
import joblib
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
import time


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

global in_process_list
in_process_list = []
global lea_order
lea_order = None
# Load the scaler and model
scaler = joblib.load('scaler.pkl')
model = joblib.load('final_model.pkl')

ORION_LD_URL = os.getenv("ORION_LD_URL", "localhost")
ORION_LD_PORT = os.getenv("ORION_LD_PORT", 1026)
CONTEXT_URL = os.getenv("CONTEXT_URL", "context")
CONTEXT_PORT = os.getenv("CONTEXT_PORT", 5051)

POLIMI_ORION_LD_URL = os.getenv("ORION_LD_URL", "localhost")
POLIMI_CONTEXT_URL = os.getenv("POLIMI_CONTEXT_URL", "context")
POLIMI_ORION_LD_PORT = os.getenv("POLIMI_ORION_LD_PORT", 1026)
auth_token = None
#################################################################################################
# Function to parse productionStartTime
def parse_time(item):
    return datetime.strptime(item["productionStartTime"], "%Y-%m-%dT%H:%M:%S.%fZ")



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
    # Scale the sample using the loaded scaler
    sample_scaled = scaler.transform(input_val)

    # Predict
    prediction = model.predict(sample_scaled)

    return True if prediction[0] == 1 else False

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


def ml_pipeline():
    n = 3
    incomplete_orders_list, in_process_list, complete_orders_list = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    queue_size, process_stat =  len(incomplete_orders_list), 1 if len(in_process_list) > 0 else 0 # first input, and thrid input 
    if process_stat:
        start_time = in_process_list[0]["productionStartTime"]
        quantity = orderQuantity(in_process_list) 
        # Get the current time in UTC
        now = datetime.now(timezone.utc)

        # Compute the difference
        time_diff = now - start_time

        # Get the difference in minutes
        minutes_diff = time_diff.total_seconds() / 60
        
        # time_to_finish = quantity*7.5 + 3 -(datetime.now() - start_time) # the time difference should be in minutes
        time_to_finish = quantity*7.5 + 3 - (minutes_diff) # the time difference should be in minutes

        all_list = incomplete_orders_list + in_process_list + complete_orders_list

        # Sort the list (latest first)
        all_sorted = sorted(all_list, key=parse_time, reverse=True)
        # Take first N items
        top_n = all_sorted[:n]

        # Parse the times
        top_n_times = [parse_time(item) for item in top_n]

        # Calculate differences in minutes
        differences_minutes = []
        for i in range(len(top_n_times) - 1):
            diff = (top_n_times[i] - top_n_times[i+1]).total_seconds() / 60
            differences_minutes.append(diff)

        # Calculate average difference
        if differences_minutes:
            average_inter_arrival = sum(differences_minutes) / len(differences_minutes)
        else:
            average_inter_arrival = 0
        

        #TODO complete the convertion of datetime.now() - start_time
        # DONE

        #TODO average of creationTime in all three list for top n ex 10. 
        # DONE

        # average_inter_arrival = None

        outsourcing_action = Mlprocessing([queue_size, process_stat, time_to_finish, average_inter_arrival,  quantity])

        if outsourcing_action:
            choose_top_n(incomplete_orders_list, n)
    
def ml_pipeline2():
    n = 3
    incomplete_orders_list, in_process_list, complete_orders_list = extract_entity_data(ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order")
    queue_size, process_stat =  len(incomplete_orders_list), 1 if len(in_process_list) > 0 else 0 # first input, and thrid input 
    if process_stat:
        start_time = in_process_list[0]["productionStartTime"]
        quantity = orderQuantity(in_process_list) 
        # Get the current time in UTC
        now = datetime.now(timezone.utc)

        # Compute the difference
        time_diff = now - start_time

        # Get the difference in minutes
        minutes_diff = time_diff.total_seconds() / 60
        
        # time_to_finish = quantity*7.5 + 3 -(datetime.now() - start_time) # the time difference should be in minutes
        time_to_finish = quantity*7.5 + 3 - (minutes_diff) # the time difference should be in minutes

        all_list = incomplete_orders_list + in_process_list + complete_orders_list

        # Sort the list (latest first)
        all_sorted = sorted(all_list, key=parse_time, reverse=True)
        # Take first N items
        top_n = all_sorted[:n]

        # Parse the times
        top_n_times = [parse_time(item) for item in top_n]

        # Calculate differences in minutes
        differences_minutes = []
        for i in range(len(top_n_times) - 1):
            diff = (top_n_times[i] - top_n_times[i+1]).total_seconds() / 60
            differences_minutes.append(diff)

        # Calculate average difference
        if differences_minutes:
            average_inter_arrival = sum(differences_minutes) / len(differences_minutes)
        else:
            average_inter_arrival = 0
        

        #TODO complete the convertion of datetime.now() - start_time
        # DONE

        #TODO average of creationTime in all three list for top n ex 10. 
        # DONE

        # average_inter_arrival = None

        outsourcing_action = Mlprocessing([queue_size, process_stat, time_to_finish, average_inter_arrival,  quantity])

        if outsourcing_action:
            choose_top_n(incomplete_orders_list, n)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(ml_pipeline2, 'interval', minutes=5)
    scheduler.start()
    print("Scheduler started. Running every 5 minutes.")
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")