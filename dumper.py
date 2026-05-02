#basics
import json

auto_signals = {
    "ferrari": 3, "bmw": 3, "porsche": 3, "lamborghini": 3, "tesla": 3,
    "acceleration": 2, "torque": 2, "horsepower": 2, "drivetrain": 2, "transmission": 2,
    "aerodynamics": 2, "suspension": 2, "infotainment": 1, "autopilot": 1, "test-drive": 1,
    "facelift": 1, "chassis": 1, "steering": 1, "hybrid": 1, "supercharger": 1
}

space_signals = {
    "exoplanet": 3, "supernova": 3, "blackhole": 3, "multiverse": 3, "teleportation": 3,
    "nebula": 2, "asteroid": 2, "starship": 2, "galaxy": 2, "orbit": 2,
    "spacetime": 2, "cyborg": 1, "stargate": 1, "cosmology": 1, "extraterrestrial": 1,
    "astronaut": 1, "lunar": 1, "quantum": 1, "interstellar": 1, "constellation": 1
}

food_signals = {
    "sous-vide": 3, "michelin": 3, "confectionery": 3, "saute": 3, "gastronomy": 3,
    "marinate": 2, "fermentation": 2, "caramelize": 2, "braising": 2, "seasoning": 2,
    "umami": 2, "ingredients": 1, "gourmet": 1, "spatula": 1, "preheat": 1,
    "kneading": 1, "zest": 1, "simmer": 1, "pastry": 1, "appetizer": 1
}

fit_signals = {
    "hypertrophy": 3, "calisthenics": 3, "metabolism": 3, "anaerobic": 3, "cardiovascular": 3,
    "treadmill": 2, "electrolytes": 2, "endurance": 2, "dumbbell": 2, "physiotherapy": 2,
    "protein": 1, "biceps": 1, "cholesterol": 1, "hydration": 1, "flexibility": 1,
    "workout": 1, "gym": 1, "supplement": 1, "calories": 1, "stretching": 1
}

money_signals = {
    "arbitrage": 3, "dividend": 3, "cryptocurrency": 3, "bankruptcy": 3, "liquidity": 3,
    "inflation": 2, "portfolio": 2, "mortgage": 2, "commodity": 2, "volatility": 2,
    "equity": 2, "ledger": 1, "revenue": 1, "deficit": 1, "investment": 1,
    "stocks": 1, "banking": 1, "interest": 1, "capital": 1, "recession": 1
}

nature_signals = {
    "photosynthesis": 3, "biodiversity": 3, "ecosystem": 3, "pollination": 3, "rainforest": 3,
    "habitat": 2, "conservation": 2, "migration": 2, "botany": 2, "geology": 2,
    "wetlands": 2, "endangered": 1, "wildlife": 1, "climate": 1, "tundra": 1,
    "atmosphere": 1, "organism": 1, "species": 1, "evolution": 1, "deforestation": 1
}

master_brain = {
    "Automotive": auto_signals,
    "Space": space_signals,
    "Food": food_signals,
    "Fitness": fit_signals,
    "Finance": money_signals,
    "Nature": nature_signals
}

with open("signals.json", "w", encoding="utf-8") as f:
    json.dump(master_brain, f, indent=4)
