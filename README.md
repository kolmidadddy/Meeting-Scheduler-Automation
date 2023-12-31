# Meeting Scheduler Automation
This application provides an interface to manage user login and scheduling systems. It uses MongoDB for data storage and integrates with a calendar system to fetch and update calendar entries.

## Getting Started
Before running the application, ensure you have the required environment variables set up. The application uses .env files to manage sensitive credentials, so make sure you have a .env file in your root directory with the necessary variables.

### Prerequisites/Requirements
- Python 3.x
- Flask
- APScheduler
- dotenv
- Dateutil
- Matplotlib
- pymongo

### Dependencies
+ Google Calendar API enabled and credentials.json file in the project directory.
+ MongoDB Atlas cluster or a local MongoDB server.


### Installation
1. Clone the repository:
```bash
git remote add origin https://github.com/kolmidadddy/Meeting-Scheduler-Automation.git
```

2. Install the required Python packages

3. Set up your .env file in the root directory with the following content: 
(Make sure to replace your_mongodb_password with your actual MongoDB password.)
```bash
MONGODB_PWD=your_mongodb_password
```
4. Install all dependencies with pip:
```bash
pip install pymongo google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dotenv 
```

## Application Structure
### Main Application (app.py)
The main application initializes the Flask application, sets up routes, and manages MongoDB connections. It integrates with a calendar utility and regularly updates calendar data. A background scheduler is used to fetch and update calendar data at regular intervals.

Key Features:

+ User authentication (login/logout)
+ Calendar data refresh
+ Secure routing with login requirements

### User Routes
This file defines user-related routes:

+ Sign Up
+ Sign Out
+ Login
+ Schedule Meeting (lets-meet)
It also provides functionality to plot users' busy slots and find the soonest available slot for a meeting.

## Running the Application
To run the application locally:
```bash
python app.py
```

This starts the Flask development server on 127.0.0.1 at port 5000.

## Contributing 
For any enhancement or bug fixes, please raise an issue or submit a pull request

