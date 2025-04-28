import requests
import logging
# Orion-LD Configuration



logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_entity(ORION_HOST, ORION_PORT, ENTITY_ID, context, context_port):
    """Fetch the current state of the queue entity from Orion-LD."""
    url = f"http://{ORION_HOST}:{ORION_PORT}/ngsi-ld/v1/entities/{ENTITY_ID}?options=keyValues"
    headers = {
  'Link': f'<http://{context}:{context_port}/ngsi-context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"',
  'Accept': 'application/json'
}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info("Successfully fetched entity data.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch entity: {e}")
        return None

def _split_data_on_status(data):
    """Split the data into three lists based on the orderStatus attribute."""
    incomplete_orders = []
    processing_orders = []
    completed_orders = []
    for order in data:
        if order["orderStatus"] == "NOTSTARTED":
            incomplete_orders.append(order)
        elif order["orderStatus"] == "INPROGRESS":
            processing_orders.append(order)
        elif order["orderStatus"] == "COMPLETED":
            completed_orders.append(order)

    return incomplete_orders, processing_orders, completed_orders


def extract_entity_data(ORION_LD_HOST, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT, ENTITY_TYPE="Order"):
    """Fetch the current state of the queue entity from Orion-LD."""
    url = f"http://{ORION_LD_HOST}:{ORION_LD_PORT}/ngsi-ld/v1/entities?type={ENTITY_TYPE}&options=keyValues&limit=1000"
    headers = {
        'Link': f'<http://{CONTEXT_URL}:{CONTEXT_PORT}/ngsi-context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"',
        'Accept': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info("Successfully fetched entity data.")
        return _split_data_on_status(response.json())  # returns 3 lists
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch entities: {e}")
        return [], [], []  # <- FIX HERE

    

def _patch_entity_id_inprocess(entityid, ORION_HOST, ORION_PORT,  context, context_port,timestamp):
    """Extract the entity ID from the entity list."""
    url = f"http://{ORION_HOST}:{ORION_PORT}/ngsi-ld/v1/entities/{entityid}/attrs"
    headers = {
        'Content-Type': "application/json",
        "Link": f'<http://{context}:{context_port}/ngsi-context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
    }

    update_payload = {
        "orderStatus": {
            "type": "Property",
            "value": "INPROGRESS"
        },  
         "productionLocation": {
              "type": "Property",
              "value": "INHOUSE"
         },
          "productionStartTime": {
              "type": "Property",
              "value": timestamp
        }
                    }

    try:
        response = requests.patch(url, json=update_payload, headers=headers)
        response.raise_for_status()
        logger.info("Successfully updated processingOrderList.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update entity: {e}")
        return False


    
def update_processing_order_list(updated_list, ORION_HOST, ORION_PORT, context, context_port,timestamp):
    """Update the processingOrderList attribute in Orion-LD."""
    for order in updated_list:
        if not _patch_entity_id_inprocess(order["id"], ORION_HOST, ORION_PORT, context, context_port,timestamp):
            return False
    return True





def _patch_entity_id_inprocess_outsource(entityid, ORION_HOST, ORION_PORT,  context, context_port,timestamp):
    """Extract the entity ID from the entity list."""
    url = f"http://{ORION_HOST}:{ORION_PORT}/ngsi-ld/v1/entities/{entityid}/attrs"
    headers = {
        'Content-Type': "application/json",
        "Link": f'<http://{context}:{context_port}/ngsi-context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
    }

    update_payload = {
        "orderStatus": {
            "type": "Property",
            "value": "INPROGRESS"
        },  
         "productionLocation": {
              "type": "Property",
              "value": "OUTSOURCE"
         },
          "orderOutsourceTime": {
              "type": "Property",
              "value": timestamp
        }
    }

    try:
        response = requests.patch(url, json=update_payload, headers=headers)
        response.raise_for_status()
        logger.info("Successfully updated processingOrderList.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update entity: {e}")
        return False


    
def update_outsource_processing_order_list(updated_list, ORION_HOST, ORION_PORT, context, context_port,timestamp):
    """Update the processingOrderList attribute in Orion-LD."""
    for order in updated_list:
        if not _patch_entity_id_inprocess_outsource(order["id"], ORION_HOST, ORION_PORT, context, context_port,timestamp):
            return False
    return True




def _patch_entity_id_complete(entityid, ORION_HOST, ORION_PORT,  context, context_port,timestamp):
    """Extract the entity ID from the entity list."""
    url = f"http://{ORION_HOST}:{ORION_PORT}/ngsi-ld/v1/entities/{entityid}/attrs"
    headers = {
        'Content-Type': "application/json",
        "Link": f'<http://{context}:{context_port}/ngsi-context.jsonld>; rel="http://www.w3.org/ns/json-ld#context"; type="application/ld+json"'
    }

    update_payload = {
        "orderStatus": {
            "type": "Property",
            "value": "COMPLETED"
        },  
          "productionEndTime": {
              "type": "Property",
              "value": timestamp
        }
                    }

    try:
        response = requests.patch(url, json=update_payload, headers=headers)
        response.raise_for_status()
        logger.info("Successfully updated processingOrderList.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update entity: {e}")
        return False


def update_complete_order_list(in_process_list, ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT,timestamp):
    for order in in_process_list:
        if not _patch_entity_id_complete(order["id"], ORION_LD_URL, ORION_LD_PORT, CONTEXT_URL, CONTEXT_PORT,timestamp):
            return False
    return True    


def ngsi_subscribe_creation(orion, orion_port, context, context_port, notify_endpoint):
    url = f'http://{orion}:{orion_port}/ngsi-ld/v1/subscriptions/'

    headers = {
          'Content-Type': 'application/ld+json'  }

    subscription = {
    "description": "Notify me when an order is created",
    "type": "Subscription",
    "entities": [
        {
            "type": "order"
        }
    ],
    "notification": {
        "endpoint": {
            "uri": notify_endpoint,
            "accept": "application/json"
        },
        "trigger": ["create"]
    },
    "@context": f"http://{context}:{context_port}/ngsi-context.jsonld"
}

    response = requests.post(url, headers=headers, data=json.dumps(subscription))
    return response


def ngsi_subscribe_status_update(orion, orion_port, context, context_port, notify_endpoint):
    url = f'http://{orion}:{orion_port}/ngsi-ld/v1/subscriptions/'

    headers = {
          'Content-Type': 'application/ld+json'  }

    subscription = {
        "description": "Notify me when the order status changes",
        "type": "Subscription",
        "entities": [
            {
                 "type": "order"
            }
        ],
          "watchedAttributes": ["orderStatus" ],
        "notification": {
            "attributes": ["orderStatus"],  # Ensures all attributes are included
            "format": "normalized",
            "endpoint": {
                "uri": notify_endpoint,
                "accept": "application/json"
            }
        },
        "@context": f"http://{context}:{context_port}/ngsi-context.jsonld"
    }

    response = requests.post(url, headers=headers, data=json.dumps(subscription))
    return response
#UPDATE WITH @CONTEXT






def post_to_polimi_orion(entity_list):
    





