import json

got = {
    "last_reject_id": 0
}

with open("stats.json", "w") as f:
    json.dump(got,f)
