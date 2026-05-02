#Settings
import bcrypt
import os
import mysql.connector
import hashlib
from Connector import generate_id
from Connector import get_connection

db = get_connection()
cursor = db.cursor()

def change_username(user_id):
    new_username = input("Enter your new unique username: ")
    try:
        cursor.execute("UPDATE users SET username = %s WHERE user_id = %s", (new_username, user_id))
        db.commit()
        print("Username updated successfully!")
    except:
        print("That username is already taken.")

def change_password(user_id):
    if not pass_checker(user_id):
        print("Verification failed. Password change aborted.")
        return
    new_password = input("Enter new password: ")
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode()
    
    cursor.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (hashed, user_id))
    db.commit()
    print("Password changed.")

def delete_account(user_id):
    if not pass_checker(user_id):
        return False
    print("\n--- Why are you leaving? ---")
    try:
        rec = int(input("How likely are you to recommend us (1-10)? "))
        ret = int(input("Will you ever return (1-10)? "))
        reason = input("Reason (Optional): ")
        cursor.execute("""
            UPDATE users 
            SET username = NULL, status = 'deleted' 
            WHERE user_id = %s
        """, (user_id,))
        
        file_path = f"recovery_{user_id}.txt"
        if os.path.exists(file_path):
            os.remove(file_path)   
        db.commit() 
        print("\nAccount deleted. Your username is now available for others.")
        return True
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        db.rollback()
        return False
    except ValueError:
        print("Invalid input. Please enter numbers.")
        return False

def pass_checker(user_id):
    print("\n--- SECURITY VERIFICATION ---")
    password = input("Confirm your password to proceed: ").strip()
    cursor.execute("SELECT password_hash FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        stored_hash = result[0].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True
            
    print("[!] Verification failed. Action aborted.")
    return False

def manage_safety(user_id):
    if not pass_checker(user_id):
        return
    cursor.execute("SELECT question_text FROM safety WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    if result:
        current_q = result[0]
        print(f"\n[!] Current Recovery Question: '{current_q}'")
        print("1. Update Question/Answer")
        print("2. Remove Recovery Safety (Opt-out)")
        print("3. Back")
        choice = input("\nSelect: ").strip()
        if choice == '1':
            new_q = input("\nEnter new secret question: ").strip()
            new_a = input("Enter new secret answer: ").strip()
            hashed_a = hash_function(new_a) 
            cursor.execute("""
                UPDATE safety SET question_text = %s, answer_hash = %s 
                WHERE user_id = %s
            """, (new_q, hashed_a, user_id))
            db.commit()
            print("\nSafety settings updated.")
        elif choice == '2':
            cursor.execute("DELETE FROM safety WHERE user_id = %s", (user_id,))
            db.commit()
            print("\nRecovery safety removed. You have opted out.")
    else:
        print("\n--- Password Recovery Setup ---")
        new_q = input("Enter a secret question: ").strip()
        new_a = input("Enter the answer: ").strip()
        hashed_a = hash_function(new_a)
        cursor.execute("""
            INSERT INTO safety (user_id, question_text, answer_hash)
            VALUES (%s, %s, %s)
        """, (user_id, new_q, hashed_a))
        db.commit()

def view_saves(user_id):
    query = """
        SELECT h.blog_id, r.genre, r.filepath 
        FROM user_history h
        JOIN ranker r ON h.blog_id = r.id
        WHERE h.user_id = %s AND h.is_saved = 1
    """
    cursor.execute(query, (user_id,))
    saves = cursor.fetchall()

    if not saves:
        print("\nNo saved blogs yet!")
        return
    print("\n--- Your Saved Blogs ---")
    for i, (blog_id, genre, path) in enumerate(saves, 1):
        name = os.path.basename(path).replace('.txt', '').upper()
        print(f"{i}. [{genre}] {name}")
    print("\n[#] Select Number to Read | [R#] Remove (e.g. R1) | [B] Back")
    choice = input(">> ").lower().strip()
    if choice == 'b':
        return
    elif choice.startswith('r'):
        try:
            idx = int(choice[1:]) - 1
            blog_id, genre, path = saves[idx] 
            cursor.execute("""
                UPDATE user_history SET is_saved = 0 
                WHERE user_id = %s AND blog_id = %s
            """, (user_id, blog_id))
            cursor.execute("""
                UPDATE ranker SET saves = GREATEST(0, saves - 1) 
                WHERE id = %s
            """, (blog_id,))
            cursor.execute("""
                UPDATE user_interests 
                SET points = GREATEST(0, points - 5) 
                WHERE user_id = %s AND genre = %s
            """, (user_id, genre))
            db.commit()
            print(f"\nRemoved from save!")
            view_saves(user_id) 
            
        except (ValueError, IndexError):
            print("Invalid selection.")
    else:
        try:
            idx = int(choice) - 1
            blog_id, genre, path = saves[idx]
            
            print("\n" + "="*50)
            with open(path, 'r') as f:
                print(f.read())
            print("="*50)
            input("\nPress Enter to return to saves...")
            view_saves(user_id) # Loop back to list
        except (ValueError, IndexError):
            print("Invalid selection.")

def hash_function(text):
    return hashlib.sha256(text.lower().strip().encode()).hexdigest()

