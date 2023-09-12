from __future__ import print_function
from functools import wraps

import os.path
import os


from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask, flash, redirect, request, render_template, session, url_for
from calendar_util import main as calendar_main
from user.routes import user_bp

from dotenv import load_dotenv, find_dotenv
from mongodb_util import get_mongo_client

# Shortcut to load the environment variable file
load_dotenv(find_dotenv())

# To retrieve the password from env file
password = os.environ.get("MONGODB_PWD")

connection_string = f"mongodb+srv://amorelieens:{password}@cluster0.23c0zzi.mongodb.net/?retryWrites=true&w=majority"

app = Flask(__name__)
app.register_blueprint(user_bp)

app.secret_key = '79B834609EB62400'
def initialize_scheduler(client_status):
    if client_status:  # Only start scheduler if MongoDB connection is successful
        scheduler = BackgroundScheduler()
        scheduler.add_job(calendar_main, 'interval', minutes=10)  # Run every 10 minutes
        scheduler.start()
    else:
        app.logger.error("Scheduler not started due to MongoDB connection failure")


# *Database
client = get_mongo_client()
if client:
    app.db = client.user_login_system
    initialize_scheduler(True)  # Initialize scheduler when MongoDB connection is successful
else:
    app.logger.error("Failed to connect to MongoDB")
    initialize_scheduler(False)  # Do not initialize scheduler
    exit(1)

# *Decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')
    return wrap
    
# *Routers
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard/')
@login_required
def dashboard():
    print(session)  # This will show the content of the session object
    return render_template('dashboard.html')

@app.route('/refresh_calendar', methods=['POST'])
@login_required
def refresh_calendar():
    try:
        calendar_main()  # Update the calendar data
        flash('Calendar successfully refreshed', 'success')
        return redirect('lets-meet')  # Redirect back to the dashboard
    except Exception as e:
        #Handle any errors that occur during that refresh
        app.logger.error(f"An error occurred while refreshing the calendar: {e}")
        flash('An error occurred while refreshing the calendar.', 'error')
        return redirect(url_for('lets-meet'))

if __name__ == '__main__':
    calendar_main() # Perform the initial load
    client_status = bool(client)  # client will be None if not connected, otherwise it will have a value
    initialize_scheduler(client_status)
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
