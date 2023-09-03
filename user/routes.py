from datetime import datetime, time, timedelta
import logging
import os
from dateutil.parser import parse
from dotenv import find_dotenv, load_dotenv
from flask import Blueprint, request, render_template
from pymongo import MongoClient
import pymongo


# Initialize logging
logging.basicConfig(level=logging.INFO)
# Shortcut to load the environment variable file
load_dotenv(find_dotenv())

# To retrieve the password from env file
password = os.environ.get("MONGODB_PWD")

CONNECTION_STRING = f"mongodb+srv://amorelieens:{password}@cluster0.23c0zzi.mongodb.net/?retryWrites=true&w=majority"

# Configure logging
logging.basicConfig(filename='mongo_operations.log', level=logging.ERROR)

def handle_mongo_exception(e):
    error_message = f"{type(e).__name__} : {e}"
    print(error_message)
    logging.error(error_message)

# Create a MongoDB client once and reuse it
client = None
try:
    client = MongoClient(CONNECTION_STRING)
except (pymongo.errors.ConnectionFailure, pymongo.errors.ServerSelectionTimeoutError) as e:
    handle_mongo_exception(e)

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/signup', methods=['GET','POST'])
def signup():
    from user.models import User
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        user = User(name, email, password)
        response = user.signup() 

        return response
    else:
        return render_template('signup.html')
    
    
@user_bp.route('/user/signout')
def signout():
    from user.models import User
    return User().signout()

@user_bp.route('/user/login', methods=['GET','POST'])
def login():
    from user.models import User
    if request.method == 'POST':
        return User().login()
    else:
        return render_template('login.html')

# Reusable Function to parse datetime strings
def parse(time_str):
    try:
        modified_str = time_str.replace('T', ' ').split('+')[0]
        if ' ' in modified_str:
            return datetime.strptime(modified_str, '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.strptime(modified_str, '%Y-%m-%d')
    except Exception as e:
        return None
    

# Function to convert preference slots to datetime objects
def convert_to_datetime(preference_slots, day_start):
    try:
        return [
            (
                day_start.replace(hour=int(start_hr), minute=int(start_min)),
                day_start.replace(hour=int(end_hr), minute=int(end_min))
            )
            for start_str, end_str in (slot.split('-') for slot in preference_slots)
            for start_hr, start_min in (start_str.split(':'))
            for end_hr, end_min in (end_str.split(':'))
        ]
    except Exception as e:
        return []

    
# Function to find available slots
def find_available_slots(busy_slots, day_start, day_end, preference_slots):
    available_slots = []
    
    # Convert preference slots to datetime objects
    preference_slots_dt = []
    for slot in preference_slots:
        start_str, end_str = slot.split("-")
        start_hr, start_min = map(int, start_str.split(":"))
        end_hr, end_min = map(int, end_str.split(":"))

        preference_slots_dt.append((
            day_start.replace(hour=start_hr, minute=start_min),
            day_start.replace(hour=end_hr, minute=end_min)
        ))

    for pref_start, pref_end in preference_slots_dt:
        current_start = max(day_start, pref_start)
        current_end = None

        for time_str, action in sorted(busy_slots):
            time = datetime.fromisoformat(time_str)

            if time < pref_start or time > pref_end:
                continue

            if action == 'start':
                current_end = max(current_end, time) if current_end else time
            elif action == 'end':
                current_start = max(current_start, time)
                if current_end and current_start >= current_end:
                    slot_start = current_end
                    slot_end = current_start
                    if slot_end > slot_start:
                        available_slots.append((slot_start, slot_end))
                    current_end = None

        if current_start < pref_end:
            slot_start = max(current_start, pref_start)
            slot_end = min(pref_end, day_end)
            if slot_end > slot_start:
                available_slots.append((slot_start, slot_end))

    return available_slots

# Route to schedule meeting
@user_bp.route('/user/lets-meet', methods=['GET', 'POST'])
def schedule_meeting():
    client = MongoClient(CONNECTION_STRING) 
    db = client.calendar_db
    users_collection = db.users

    # Fetch only a subset of users for pagination
    all_users = list(users_collection.find({}).limit(50))

    upcoming_events = {}
    available_slots_by_user = {}
    preference_slots_by_user = {}
    error_message = None

    if request.method == 'POST':
        try:
            selected_user_emails = request.form.getlist("selected_users")
            selected_date = request.form.get("date")

            if not selected_user_emails:
                error_message = "Please select at least one user."
            elif not selected_date:
                error_message = "Please select a date."
            else:
                dt = parse(selected_date)
                if dt is None:
                    raise ValueError("Invalid date format")

                dt_start = datetime.combine(dt, time.min)
                dt_end = datetime.combine(dt, time.max)

                for email in selected_user_emails:
                    user_info = users_collection.find_one({"email": email})
                    if not user_info:
                        logging.warning(f"No user found for email: {email}")
                        continue

                    preference_slots = user_info.get("preference_slots", [])
                    preference_slots_dt = convert_to_datetime(preference_slots, dt_start)
                    preference_slots_by_user[email] = preference_slots

                    events_collection = db.get_collection(user_info.get("collection_name", ""))
                    if events_collection is None:
                        logging.error(f"No collection found for user {email}")
                        continue

                    cursor = events_collection.find(
                        {"start_time": {"$gte": dt_start}, "end_time": {"$lte": dt_end}}
                    ).sort("start_time", 1)

                    events = list(cursor)
                    upcoming_events[email] = events

                    busy_slots_for_user = [
                        (event['start_time'], 'start') for event in events
                    ] + [
                        (event['end_time'], 'end') for event in events
                    ]

                    available_slots = find_available_slots(busy_slots_for_user, dt_start, dt_end, preference_slots_dt)
                    available_slots_by_user[email] = [(str(start), str(end)) for start, end in available_slots]

        except ValueError as ve:
            logging.error(f"Value error: {ve}")
            error_message = "Invalid input."
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            error_message = "An unexpected error occurred."

    return render_template(
        'lets-meet.html',
        all_users=all_users,
        upcoming_events=upcoming_events,
        available_slots_by_user=available_slots_by_user,
        preference_slots_by_user=preference_slots_by_user,
        error_message=error_message
    )