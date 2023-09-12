import logging
import os
import pymongo
from dateutil.parser import parse
from dotenv import find_dotenv, load_dotenv
from flask import Blueprint, request, render_template
from pymongo import MongoClient


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

@user_bp.route('/user/lets-meet', methods=['GET','POST'])
def lets_meet():
    from datetime import datetime, timedelta
    from dateutil.parser import parse

    def find_soonest_slot(busy_slots, duration, after_time=None):
        merged_slots = []
        for slots in busy_slots.values():
            merged_slots.extend(slots)
        merged_slots.sort(key=lambda x: x['start_time'])

        current_time = datetime.utcnow()
        if after_time:
            current_time = max(current_time, parse(after_time))

        for i in range(len(merged_slots) - 1):
            gap = merged_slots[i+1]['start_time'] - merged_slots[i]['end_time']
            if gap >= duration and current_time <= merged_slots[i]['end_time']:
                return merged_slots[i]['end_time'], merged_slots[i]['end_time'] + duration
        
        # If no slot is found within the busy times, return the time after the last busy slot
        if merged_slots:
            return merged_slots[-1]['end_time'], merged_slots[-1]['end_time'] + duration
        else:
            return current_time, current_time + duration

    if request.method == 'POST':
        # Getting multiple email inputs from the form
        emails = request.form.getlist('email')

        # Assuming a default meeting duration of 1 hour. 
        duration = timedelta(hours=int(request.form.get('duration', 1)))

        if not emails:
            return render_template('lets-meet.html', error_message="No email provided.")

        # Create a MongoDB client once and reuse it
        client = MongoClient(CONNECTION_STRING)
        db = client['calendar_db']
        user_collection = db['users']

        # Fetching busy slots of the users based on the email addresses
        user_slots = {}
        for email in emails:
            user_data = user_collection.find_one({"email": email})
            if user_data and 'busy_slots' in user_data:
                user_slots[email] = user_data['busy_slots']

        # Check if we are looking for a slot after a certain time
        after_time = request.form.get('after_time', None)
        start, end = find_soonest_slot(user_slots, duration, after_time=after_time)
        meeting_slot = f"{start.strftime('%A %I%p, %d/%m/%Y')} to {end.strftime('%A %I%p, %d/%m/%Y')}"

        return render_template('lets-meet.html', user_slots=user_slots, meeting_slot=meeting_slot, emails=emails)
    else:
        return render_template('lets-meet.html', user_slots={}, meeting_slot=None, emails=[])
