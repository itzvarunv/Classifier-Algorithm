import Verification
import Settings
import Engine
import Connector
import sys

def main():
    print("----------------------------------")
    print("             CURIO                ")
    print("    Feed your curiosity.          ")
    print("----------------------------------")
    current_user = None
    while not current_user:
        print("\n1. Sign In")
        print("2. Sign Up")
        print("3. Forgot Password?")
        print("4. Exit")
        choice = input("\nSelect (1-4): ").strip()
        if choice == '1':
            success, user_id = Verification.SignIn()
            if success:
                current_user = user_id
        elif choice == '2':
            success, user_id = Verification.SignUp()
            if success:
                current_user = user_id 
        elif choice == '3':
            Verification.forgot_password()
        
        elif choice == '4':
            print("Goodbye!")
            sys.exit()
    curio_dashboard(current_user)

def curio_dashboard(user_id):
    session_interests = set()
    while True:
        print("\n========================")
        print("      CURIO HOME        ")
        print("========================")
        print("[F]eed      - Recommended")
        print("[D]iscovery - Explore New")
        print("[S]aves     - Your Library")
        print("[O]ptions   - Settings")
        print("[L]ogout")
        choice = input("\n> ").strip().lower()
        if choice == 'f':
            start_reading_loop(user_id, session_interests)    
        elif choice == 'd':
            discovery_hub(user_id, session_interests)
        elif choice == 's':
            Settings.view_saves(user_id)            
        elif choice == 'o':
            status = options_menu(user_id)
            if status == "DELETED":
                break                
        elif choice == 'l':
            if session_interests:
                Engine.apply_session_growth(user_id, session_interests)
            break

def start_reading_loop(user_id, session_interests):
    while True:
        result = Engine.get_recommended_blog_v2(user_id) 
        if result:
            blog_id, genre, path = result
            if not view_single_blog(user_id, blog_id, genre, session_interests, path):
                break
        else:
            print("\n[!] No more blogs in your feed right now!")
            break
        
def discovery_hub(user_id, session_interests):
    while True:
        print("\n--- Discovery Hub ---")
        print("1. Explore New")
        print("2. People Like You")
        print("3. Back")
        choice = input("\nSelect: ").strip()
        if choice == '1':
            while True:
                res = Connector.fetch_discovery_data(user_id)
                if res:
                    if not view_single_blog(user_id, res[0], res[1], session_interests, res[2], is_discovery=True):
                        break
                else:
                    print("\n[!] Vault empty!")
                    break
        elif choice == '2':
            while True:
                peer_id = Engine.get_peer_recommendation(user_id)
                if peer_id in ["SOLO_EXPLORER", "TRAILBLAZER"]:
                    print(f"\n[!] {peer_id}: Not enough peer data yet.")
                    input("Press Enter...")
                    break
                res = Connector.fetch_collaborative_data(user_id, peer_id)
                if res:
                    if not view_single_blog(user_id, res[0], res[1], session_interests, res[2], is_discovery=True):
                        break
                else:
                    print("\n[!] You've read everything your peers liked!")
                    input("Press Enter...")
                    break
        elif choice == '3':
            break
            
def options_menu(user_id):
    while True:
        print("\n--- CURIO SETTINGS ---")
        print("1. Change Username")
        print("2. Change Password")
        print("3. Set Recovery Question")
        print("4. Delete Account")
        print("5. Back")
        
        choice = input("\nSelect: ").strip()

        if choice == '1':
            Settings.change_username(user_id)
        elif choice == '2':
            Settings.change_password(user_id)
        elif choice == '3':
            Settings.manage_safety(user_id)
        elif choice == '4':
            if Settings.delete_account(user_id):
                return "DELETED"
        elif choice == '5':
            break
        
def view_single_blog(user_id, blog_id, genre, session_interests, f_path, is_discovery=False):
    try:
        with open(f_path, 'r') as f:
            print(f"\n--- {genre.upper()} ---")
            print(f.read())
    except Exception as e:
        print(f"\n[!] Error loading file at {f_path}: {e}")
        return True 
    print("-" * 30)
    action = input("\n[L]ike | [D]islike | [S]ave | [N]ext | [E]xit: ").lower().strip()
    if action == 'l':
        if is_discovery:
            Engine.log_discovery_like(user_id, blog_id, genre) # Specialized +15 points
        else:
            Engine.log_interaction(user_id, blog_id, genre, 'like')
        session_interests.add(genre)
    elif action == 'd':
        if is_discovery:
            Engine.log_discovery_dislike(user_id, blog_id, genre) # Specialized -10 points
        else:
            Engine.log_interaction(user_id, blog_id, genre, 'dislike')
    elif action == 's':
        Engine.log_interaction(user_id, blog_id, genre, 'save')
        session_interests.add(genre)
    elif action == 'e':
        return False   
    return True

if __name__ == "__main__":
    main()
