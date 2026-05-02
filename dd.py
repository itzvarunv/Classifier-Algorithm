import json

upload_counts = {"Automotive": 0, "Space": 0, "Food": 0, "Fitness": 0, "Finance": 0, "Nature": 0, "Noise": 0}

with open("meta.json", "w") as f:
    json.dump(upload_counts, f, indent=4)
