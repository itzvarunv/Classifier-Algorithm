#File dumper
import mysql.connector
import os
import json
import difflib
import shutil
import string
import random

db_connection = mysql.connector.connect(
    host="localhost",      
    user="root",          
    password="Ferrari!", 
    database="classifier" 
)

cursor = db_connection.cursor()

with open("signals.json", "r", encoding="utf-8") as f:
    master_brain = json.load(f)

with open("meta.json", "r") as f:
    upload_counts = json.load(f)

hot_niches = sorted(
    [item for item in upload_counts.items() if item[0] != "Noise"],
    key=lambda x: x[1], 
    reverse=True
)

VAULT_DIR = "Vault"
NOISE_DIR = "Noise"
STATS_FILE = "stats.json"

def get_and_update_reject_id():
    if not os.path.exists(STATS_FILE):
        data = {"last_reject_id": 0}
    else:
        with open(STATS_FILE, "r") as f:
            data = json.load(f)
    data["last_reject_id"] += 1
    new_id = data["last_reject_id"]
    with open(STATS_FILE, "w") as f:
        json.dump(data, f)
    return new_id

def denser(content, master_brain, selection):
    valid = True
    refer = master_brain[selection]
    clean_words = [w.strip('.,!?;:').lower() for w in content.split()]
    total = len(clean_words)
    count = 0
    for word in clean_words:
        word = word.lower()
        if word.lower() in refer:
            count+=1
        else:
           potential = difflib.get_close_matches(word, refer.keys(), n=1, cutoff=0.8)
           if potential:
               count+=1
    try:
        density = (count/total)*100
    except:
        print("Spammy content detected!")
        density = None
        valid = False
    return density, valid
    

def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=11))

for niche, count in hot_niches:
    if not os.path.exists(niche):
        continue
    files = os.listdir(niche)
    for filename in files:
        if filename.startswith('.'):
            continue 
        current_file_path = os.path.join(niche, filename)
        with open(current_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        density, valid = denser(content, master_brain, niche)
        if valid and 1 <= density <= 30:
            success = False
            while not success:
                new_id = generate_id()
                vault_path = os.path.join(VAULT_DIR, f"{new_id}.txt")
                try:
                    sql = """INSERT INTO ranker 
                             (id, filepath, points, saves, views, likes, dislikes, status, genre) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    val = (new_id, vault_path, 0, 0, 0, 0, 0, 'Active', niche)
                    cursor.execute(sql, val)
                    shutil.move(current_file_path, vault_path)
                    db_connection.commit()
                    success = True
                    print(f"Verified & Stored: {new_id}")
                    print(f"File: {filename} | Density: {density}% | Niche: {niche}")
                except mysql.connector.Error as err:
                    if err.errno == 1062: 
                        print(f"Collision on {new_id}, regenerating...")
                        db_connection.rollback()
                    else:
                        print(f"Database Error: {err}")
                        db_connection.rollback()
                        break 
        else:
            reject_id = get_and_update_reject_id() 
            reject_filename = f"Reject_{reject_id}.txt" 
            shutil.move(current_file_path, os.path.join(NOISE_DIR, reject_filename))
            print(f"Rejected: {filename} moved to Noise as {reject_filename}")
db_connection.close()



