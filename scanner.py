#New Niche Creator
import os
import json

STOP_WORDS = {
    'the', 'is', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'as', 'at', 
    'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 
    'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 
    'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 
    'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now',
    'your', 'this', 'that', 'with', 'from', 'they', 'have', 'been', 'were', 'those' 
}


blacklist_signals = {
    "free": -5, "buy": -5, "promo": -5, "discount": -5, 
    "click": -5, "subscribe": -5, "offer": -5, "win": -5
}

def gatekeeper_scorer(content, signals, blacklist):
    score = 0
    words = [w.strip('.,!?;:').lower() for w in content.split()]
    for word in words:
        if word in signals:
            score += signals[word]
        if word in blacklist:
            score += blacklist[word]        
    return score

def safety_check(content):
    RED_FLAGS = ["bomb", "robbery", "heist", "extremism", "kill"]
    words = [w.strip('.,!?;:').lower() for w in content.split()]
    total_words = len(words)
    red_flag_count = sum(1 for w in words if w in RED_FLAGS)
    danger_density = (red_flag_count / total_words) * 100
    if danger_density > 2.0:
        return "DANGEROUS"
    return "SAFE"

def build_discovery_map(folder_path, stop_words):
    discovery_map = {}
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    for filename in files:
        if filename.startswith('.'):
            continue     
        try:
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8', errors='ignore') as f:
                words = set([w.strip('.,!?;:').lower() for w in f.read().split() 
                             if w.lower() not in stop_words and len(w) >= 2])
                for word in words:
                    if word not in discovery_map:
                        discovery_map[word] = []
                    discovery_map[word].append(filename)
        except Exception as e:
            print(f"Could not read {filename}: {e}")        
    return discovery_map

def find_co_occurrences(discovery_map, min_file_spread=2):
    clusters = []
    sorted_words = sorted(discovery_map.items(), key=lambda x: x[1][0], reverse=True)
    processed_words = set()
    for word, data in sorted_words:
        if word in processed_words or data[0] < min_file_spread:
            continue
        current_files = set(data[1])
        new_niche_words = [word]
        for other_word, other_data in sorted_words:
            if other_word == word: continue
            shared_files = current_files.intersection(set(other_data[1]))
            if len(shared_files) / len(current_files) > 0.5:
                new_niche_words.append(other_word)
                processed_words.add(other_word)
        clusters.append({"keywords": new_niche_words, "files": list(current_files)})
    return clusters

def prune_niche(cluster_data, folder_path):
    final_keywords = []
    file_list = cluster_data["files"]
    for word in cluster_data["keywords"]:
        count_in_cluster = 0
        for filename in file_list:
            with open(os.path.join(folder_path, filename), 'r') as f:
                if word in f.read().lower():
                    count_in_cluster += 1
        if (count_in_cluster / len(file_list)) >= 0.4:
            final_keywords.append(word)       
    return final_keywords

def grade_niche_keywords(keywords, cluster_files, folder_path):
    graded_dict = {}
    for word in keywords:
        appearances = 0
        for filename in cluster_files:
            with open(os.path.join(folder_path, filename), 'r') as f:
                if word in f.read().lower():
                    appearances += 1
        influence = appearances / len(cluster_files)
        if influence >= 0.9: 
            graded_dict[word] = 3  # High influence (Signature Word)
        elif influence >= 0.6:
            graded_dict[word] = 2  # Medium influence
        else:
            graded_dict[word] = 1  # Low influence (Supporting word)       
    return graded_dict

def generate_niche_title(graded_dict):
    top_words = [word for word, grade in graded_dict.items() if grade == 3]
    if len(top_words) >= 2:
        return f"{top_words[0].capitalize()} & {top_words[1].capitalize()}"
    return top_words[0].capitalize() if top_words else "New Discovery"


def run_scanner(folder_path):
    print(f"--- Starting Niche Discovery in '{folder_path}' ---")
    discovery_map = build_discovery_map(folder_path, STOP_WORDS)
    potential_groups = find_co_occurrences(discovery_map)
    for group in potential_groups:
        with open(os.path.join(folder_path, group["files"][0]), 'r', encoding='utf-8', errors='ignore') as f:
            if safety_check(f.read()) == "DANGEROUS":
                continue
        graded_signals = grade_niche_keywords(group["keywords"], group["files"], folder_path)
        if len(graded_signals) >= 5:
            title = generate_niche_title(graded_signals)
            print(f"\n✨ POTENTIAL NICHE DISCOVERED: {title} ({len(group['files'])} files)")
            
            confirm = input(f"Add '{title}' to signals.json and move files? (y/n): ")
            if confirm.lower() == 'y':
                update_master_files(title, graded_signals, folder_path, group["files"])
                print(f"✅ System Updated. Niche '{title}' is now live.")
                print("Exiting to refresh Noise folder...")
                return 
            else:
                print("❌ Proposal ignored.")

def update_master_files(niche_title, graded_signals, folder_path, cluster_files):
    """The Storage Station: Injects new niche data into JSON and creates folders."""
    with open("signals.json", "r+", encoding="utf-8") as f:
        data = json.load(f)
        data[niche_title] = graded_signals
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()
    with open("meta.json", "r+", encoding="utf-8") as f:
        meta = json.load(f)
        meta[niche_title] = len(cluster_files) # Start count at current file total
        f.seek(0)
        json.dump(meta, f, indent=4)
        f.truncate()
    if not os.path.exists(niche_title):
        os.makedirs(niche_title)
    for i, filename in enumerate(cluster_files):
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(niche_title, f"{i}.txt")
        os.rename(old_path, new_path)

def run_scanner(folder_path):
    print(f"--- Starting Niche Discovery in '{folder_path}' ---")
    discovery_map = build_discovery_map(folder_path, STOP_WORDS)
    potential_groups = find_co_occurrences(discovery_map)
    moved_files = set()
    for group in potential_groups:
        remaining_files = [f for f in group["files"] if f not in moved_files]
        if len(remaining_files) < 3: 
            continue
        file_to_check = os.path.join(folder_path, remaining_files[0])
        if not os.path.exists(file_to_check):
            continue
        with open(file_to_check, 'r', encoding='utf-8', errors='ignore') as f:
            if safety_check(f.read()) == "DANGEROUS":
                continue
        graded_signals = grade_niche_keywords(group["keywords"], remaining_files, folder_path)
        
        if len(graded_signals) >= 5:
            title = generate_niche_title(graded_signals)
            print(f"\n✨ POTENTIAL NICHE DISCOVERED: {title} ({len(remaining_files)} files)")
            
            confirm = input(f"Add '{title}' to SQL Vault and move files? (y/n): ")
            if confirm.lower() == 'y':
                update_master_files(title, graded_signals, folder_path, remaining_files)
                moved_files.update(remaining_files)
                print(f"✅ System Updated. Niche '{title}' is now live in Vault.")
            else:
                print("❌ Proposal ignored.")
if __name__ == "__main__":
    run_scanner("Noise")

