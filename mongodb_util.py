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

def insert_busy_slots_to_mongo(client, occupied_slots, email):
    if client is None:
        print("MongoDB client is not initialized.")
        return None

    try:
        database_name = client.calendar_db
        collection_name = database_name.busy_slotsDB

        inserted_ids = []
        for start, end in occupied_slots:
            existing_slot = collection_name.find_one({"email": email, "start_time": start, "end_time": end})
            if existing_slot is None:
                result = collection_name.insert_one({"email": email, "start_time": start, "end_time": end})
                inserted_ids.append(result.inserted_id)

        return inserted_ids  # Optionally return IDs for further use

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
    
def insert_available_slots(client, email, available_slots):
    if client is None:
        print("MongoDB client is not initialized.")
        return None
    
    try:
        db = client.calendar_db
        coll = db.available_slotsDB
        coll.update_one({'email': email}, {'$set': {'slots': available_slots}}, upsert=True)
    except Exception as e:
        handle_mongo_exception(e)

def insert_preference_slots(client, email, preference_slots):
    if client is None:
        print("MongoDB client is not initialized.")
        return None

    try:
        db = client.calendar_db
        coll = db.preference_slotsDB
        coll.update_one({'email': email}, {'$set': {'slots': preference_slots}}, upsert=True)
    except Exception as e:
        handle_mongo_exception(e)