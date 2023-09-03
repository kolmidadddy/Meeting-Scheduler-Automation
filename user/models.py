import uuid
import bcrypt

# from main import db
from flask import current_app as app
from flask import Flask, jsonify, request, session, redirect


class User:
    def start_session(self,user):
        if 'password' in user:
            del user['password']
        # del user['password']
        session['logged_in'] = True
        session['user'] = user
        return redirect('/dashboard')
    
    def __init__(self, name=None, email=None, password=None):
        self._id = uuid.uuid4().hex
        self.name = name
        self.email = email
        # Check if the password is provided to hash it
        if password:
            self.password = self.hash_password(password)
        else:
            self.password = None
        
        
    def hash_password(self, password):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')  # Convert bytes to string before returning


    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)


    def save_to_db(self):
        # Logic to save user to database
        # For now, just a placeholder
        print("User saved to database!")
    
    def signup(self):
        self.save_to_db()  # Saving the user instance to the database
        user ={
            "_id": self._id,
            "name": self.name,
            "email": self.email,
            "password":self.password #storing the hashed password
        }
        
        if app.db.users.find_one({ "email": user['email']}):
            return jsonify({"error":"Email address already in use" }), 400
        
        # commented out return and added this clause
        if app.db.users.insert_one(user):
           self.start_session(user)
        #    return "Signup successful! Now redirecting...", 200
           return redirect('/dashboard')
            
        return jsonify({"error":"Signup failed"}),400
        # return jsonify(user)
    
    def signout(self):
        session.clear()
        return redirect('/')
    
    def login(self):
        user = app.db.users.find_one({
            "email": request.form.get('email')
        })

        print("Found user:", user)  # Check if a user is returned from the database

        # Verifying password using bcrypt
        if user and bcrypt.checkpw(request.form.get('password').encode('utf-8'), user['password'].encode('utf-8')):
            return self.start_session(user)

        return jsonify({"error": "Invalid login credentials"}), 401


