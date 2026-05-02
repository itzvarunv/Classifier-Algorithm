#Classifier
import os
import json
import difflib

with open("signals.json", "r", encoding="utf-8") as f:
    master_brain = json.load(f)

with open("meta.json", "r") as f:
    upload_counts = json.load(f)

def scorer(content, master_brain, weight):
    scores = {category: 0 for category in master_brain.keys()}
    for word in content.lower().split():
        for category, signals in master_brain.items():
            if word in signals:
                scores[category] += signals[word] * weight
            else:
                potential = difflib.get_close_matches(word, signals.keys(), n=1, cutoff=0.8)
                if potential:
                    scores[category] += signals[potential[0]] * weight
    return scores

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
    
    
    
while True:
    print("Select 1 to write your own blog")
    print("Select 2 to exit")
    while True:
        try:
            ch1 = int(input("What do you choose?: "))
            break
        except:
            print("Please enter as integer!")
    if ch1 == 1:
        title = input("What's the title?: ")
        content = input("Write what you want as a blog: ")
        title_score = scorer(title, master_brain, 3)
        ranked_results = sorted(title_score.items(), key=lambda item: item[1], reverse=True)
        winner_name = ranked_results[0][0]
        winner_score = ranked_results[0][1]
        runner_up_name = ranked_results[1][0]
        runner_up_score = ranked_results[1][1]
        tie = False
        gap = winner_score - runner_up_score
        if gap > 5:
            pass
        else:
            tie = True
        if tie == False:
            density, valid = denser(content, master_brain, winner_name)
        else:
            density1,valid1 = denser(content, master_brain, winner_name)
            density2, valid2 = denser(content, master_brain, runner_up_name)
            if valid1 == True and valid2 == True:
                if density1 > density2:
                    density = density1
                    valid = valid1
                else:
                    density = density2
                    valid = valid2
                    winner_name = runner_up_name
        if valid == True:
            noise = False
            if density < 1 or density >30:
                noise = True
            if noise == True:
                winner_name = "Noise"
            filename = str(upload_counts[winner_name]) + ".txt"
            upload_counts[winner_name] = upload_counts[winner_name] + 1
            path = os.path.join(winner_name, filename)
            with open("meta.json", "w") as f:
                json.dump(upload_counts, f, indent=4)
            with open(path, "w") as f:
                execute = title + '\n' + content
                f.write(execute)
                
        else:
            print("Couldn't upload try again!")
        print()

    elif ch1 == 2:
        print("Goodbye ;)")
        break

    else:
        print("Please enter a valid choice!")
        print()
                
                
                
                    
                
        
            
            
                
            
            
            
            
            
            
    
            
