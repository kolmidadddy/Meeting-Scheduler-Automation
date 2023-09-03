from __future__ import print_function
import datetime
import logging
import pymongo
import os.path
import os

from dotenv import load_dotenv, find_dotenv
from pymongo import MongoClient

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError


 # ! If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events.readonly',
    'https://www.googleapis.com/auth/calendar.settings.readonly'
]


# Shortcut to load the environment variable file
load_dotenv(find_dotenv())

# To retrieve the password from env file
password = os.environ.get("MONGODB_PWD")

connection_string = f"mongodb+srv://amorelieens:{password}@cluster0.23c0zzi.mongodb.net/?retryWrites=true&w=majority"


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar and shared calendars.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Connect to MongoDB
        client = MongoClient(connection_string)
        database_name = client.calendar_db # Accessing the database
        
        # Create or access a 'users' collection
        users_collection = database_name['users']
        
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        
        # List of calendar IDs, starting with 'primary' for the primary calendar
        calendar_ids = ['primary', 'manthalok@gmail.com', 'tjunwei3@gmail.com']
        
        for calendar_id in calendar_ids:
            events_result = service.events().list(
                calendarId=calendar_id, timeMin=now,
                maxResults=30, singleEvents=True,
                orderBy='startTime').execute()
            events = events_result.get('items', [])
            occupied_slots = []

            if not events:
                print(f'No upcoming events found in the calendar {calendar_id}.')
            else:
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    occupied_slots.append((start, end))
                    #print(start, event.get('summary','Busy'))
            # Start a MongoDB session
            with client.start_session() as session:
                session.start_transaction()
                try:
                    # Create a unique MongoDB collection name for each calendar
                    collection_name = calendar_id.replace('@', '_').replace('.', '_') + "_busy_slots"
                    collection = database_name[collection_name]  # Accessing/Creating the collection
                    # Clear all existing busy slots for this calendar to avoid duplication
                    collection.delete_many({})  # <-- Delete all existing data for this calendar collection

                    busy_slots_data = [
                            {"start_time": start, "end_time": end} for start, end in occupied_slots
                        ]

                    # Insert the busy slots into the specific MongoDB collection
                    if busy_slots_data:
                        inserted_ids = []
                        for slot in busy_slots_data:
                            existing_slot = collection.find_one({"start_time": slot["start_time"], "end_time": slot["end_time"]})
                            if existing_slot is None:
                                result = collection.insert_one(slot)
                                inserted_ids.append(result.inserted_id)
                    else:
                        print(f"No occupied slots to insert for {calendar_id}.")
                            
                    # Insert the email IDs and collection names into the 'users' collection
                    user_data = {"email": calendar_id, "collection_name": collection_name}
                    users_collection.update_one({'email': calendar_id}, {'$set': user_data}, upsert=True)
                    
                    session.commit_transaction()
                except Exception as e:
                    session.abort_transaction()
                    raise e
                
    # Exception handling
    except HttpError as error:
        print('An error occurred:', error)
    except pymongo.errors.ConnectionFailure as e:
        print("Connection to MongoDB failed:", e)
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print("Server selection timeout error:", e)
    except Exception as e:
        logging.error("Transaction aborted due to: {}".format(e))
        session.abort_transaction()
        raise e


if __name__ == '__main__':
    main()