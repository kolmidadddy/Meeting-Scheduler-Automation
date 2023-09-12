import logging
from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient
import os

# Shortcut to load the environment variable file
load_dotenv(find_dotenv())

# Handle MongoDB exceptions
def handle_mongo_exception(exception):
    logging.error(f"An error occurred while interacting with MongoDB: {exception}")

def get_mongo_client():
    try:
        password = os.environ.get("MONGODB_PWD")
        if password is None:
            raise EnvironmentError("MONGODB_PWD not set in environment")
        CONNECTION_STRING = f"mongodb+srv://amorelieens:{password}@cluster0.23c0zzi.mongodb.net/?retryWrites=true&w=majority"
        client = MongoClient(CONNECTION_STRING)
        logging.info("Successfully connected to MongoDB")
        return client
    except Exception as e:
        logging.error(f"Could not connect to MongoDB: {e}")
        return None

# Configure logging
logging.basicConfig(filename='mongo_operations.log', level=logging.ERROR)

def insert_busy_slots_to_mongo(client, occupied_slots_with_heuristic, email):
    if client is None:
        print("MongoDB client is not initialized.")
        return None

    try:
        database_name = client.calendar_db
        collection_name = database_name.busy_slotsDB

        inserted_ids = []
        for slot in occupied_slots_with_heuristic:
            start = slot["start_time"]
            end = slot["end_time"]
            heuristic = slot["heuristic"]

            existing_slot = collection_name.find_one({"email": email, "start_time": start, "end_time": end})
            if existing_slot is None:
                result = collection_name.insert_one({"email": email, "start_time": start, "end_time": end, "heuristic": heuristic})
                inserted_ids.append(result.inserted_id)

        return inserted_ids

    except Exception as e:
        handle_mongo_exception(e)
        return None


def retrieve_busy_slots(client,email):
    if client is None:
        print("MongoDB client is not initialized.")
        return None

    try:
        database_name = client.calendar_db
        collection_name = database_name.busy_slotsDB

        return list(collection_name.find({"email": email}))

    except Exception as e:
        handle_mongo_exception(e)
        return None

def insert_available_slots_to_mongo(client, available_slots, email):
    if client is None:
        print("MongoDB client is not initialized.")
        return None

    try:
        database_name = client.calendar_db
        collection_name = database_name.available_slotsDB  # new collection for available slots

        inserted_ids = []
        for slot in available_slots:
            start = slot["start_time"]
            end = slot["end_time"]

            existing_slot = collection_name.find_one({"email": email, "start_time": start, "end_time": end})
            if existing_slot is None:
                result = collection_name.insert_one({"email": email, "start_time": start, "end_time": end})
                inserted_ids.append(result.inserted_id)

        return inserted_ids

    except Exception as e:
        logging.error(f"An error occurred while interacting with MongoDB: {e}")
        return None


def retrieve_available_slots(client, email):
    if client is None:
        print("MongoDB client is not initialized.")
        return None

    try:
        database_name = client.calendar_db
        # Generate the collection name based on the email
        collection_name_string = email.replace('@', '_').replace('.', '_') + "_available_slots"
        collection = database_name[collection_name_string]
        return list(collection.find({"email": email}))

    except Exception as e:
        handle_mongo_exception(e)
        return None


