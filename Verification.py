#Verification
import bcrypt
from Connector import get_connection
from Connector import generate_id
db = get_connection()
import secrets
import string
import time
import hashlib
import mysql.connector
cursor = db.cursor()
import json
from Engine import update_peer_connections
from datetime import datetime

def SignUp():
    print("Creating your new account!")
    display_name = input("What should we call you? (Display Name): ")
    while True:
        username = input("Pick a unique Username for login: ")
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            print("That username is already taken! Please try a different one.")
        else:
            break 
    password = input("Enter a password: ")
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode()
    while True:
        try:
            u_id = generate_id(length=7) 
            cursor.execute(
                "INSERT INTO users (user_id, username, display_name, password_hash, status) VALUES (%s, %s, %s, %s, 'active')",
                (u_id, username, display_name, hashed)
            )
            db.commit()
            print(f"Success! Welcome {display_name}. You can now login using your username: {username}")
            initialize_interests(u_id)
            return True, u_id 
        except mysql.connector.errors.IntegrityError:
            continue

def SignIn():
    username = input("What's your username? ")
    cursor.execute(
        "SELECT user_id, password_hash FROM users WHERE username = %s AND status = 'active'",
        (username,)
    )
    data = cursor.fetchone() 
    if data is None:
        print("User doesn't exist or account is deactivated!")
        return False, None
    stored_hash = data[1].encode('utf-8') 
    password = input("Enter password: ")
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        print("Login successful!")
        confirm = True
        user_id = data[0]
        apply_decay(user_id)
        initialize_interests(user_id)
        update_peer_connections(user_id)
    else:
        print("Wrong password!")
        confirm = False
        user_id = None     
    return confirm, user_id

def initialize_interests(user_id):
    try:
        with open("signals.json", "r") as f:
            signals = json.load(f)
            all_niches = signals.keys()
    except FileNotFoundError:
        print("Signals file not found. Skipping interest sync.")
        return
    cursor.execute("SELECT genre FROM user_interests WHERE user_id = %s", (user_id,))
    existing_records = cursor.fetchall()
    user_niche_list = [item[0] for item in existing_records]
    new_additions = 0
    for niche in all_niches:
        if niche not in user_niche_list:
            i_id = generate_id()
            cursor.execute(
            "INSERT INTO user_interests (interest_id, user_id, genre, points) VALUES (%s, %s, %s, 50)",
            (i_id, user_id, niche)
            )
            new_additions += 1
    if new_additions > 0:
        db.commit()
        print(f"Synced {new_additions} new niches to your profile.")

def forgot_password():
    username = input("Enter your username: ")
    cursor.execute("SELECT user_id FROM users WHERE username = %s AND status = 'active'", (username,))
    user_data = cursor.fetchone()    
    if not user_data:
        print(" Account not found.")
        return
    u_id = user_data[0]
    cursor.execute("SELECT question_text, answer_hash FROM safety WHERE user_id = %s", (u_id,))
    safety_data = cursor.fetchone()
    if not safety_data:
        print(" Recovery not set up.")
        return
    print(f"\nSECURITY QUESTION: {safety_data[0]}") 
    a_attempt = input("Your Answer: ").lower().strip()
    if hash_function(a_attempt) == safety_data[1]:
        print(" Identity Confirmed!")
        new_pass = input("Enter NEW password: ")
        new_hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
        cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hashed, u_id))
        db.commit()
        print(" Password updated!")
    else:
        print(" Incorrect answer.")


def apply_decay(user_id):
    cursor.execute("SELECT MAX(last_updated) FROM user_interests WHERE user_id = %s", (user_id,))
    last_log = cursor.fetchone()[0]
    if last_log:
        now = datetime.now()
        days_passed = (now - last_log).days
        if days_passed > 0:
            decay_factor = pow(0.99, days_passed)
            cursor.execute("""
                UPDATE user_interests 
                SET points = ROUND(points * %s, 5), 
                    last_updated = NOW() 
                WHERE user_id = %s
            """, (decay_factor, user_id))
            db.commit()

def hash_function(text):
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()

        
