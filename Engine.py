#Engine
import random
from Connector import generate_id
from Connector import get_connection

db = get_connection()
cursor = db.cursor()

def update_peer_connections(user_id):
    cursor.execute("""
        SELECT genre FROM user_interests 
        WHERE user_id = %s AND points > 50 
        ORDER BY points DESC LIMIT 3
    """, (user_id,))
    my_top_3 = [row[0] for row in cursor.fetchall()]
    if len(my_top_3) < 3:
        return # Not enough data yet to find true peers
    placeholders = ', '.join(['%s'] * len(my_top_3))
    query = f"""
        SELECT user_id, COUNT(*) as matches
        FROM user_interests
        WHERE genre IN ({placeholders}) AND user_id != %s AND points > 50
        GROUP BY user_id
        HAVING matches >= 3
    """
    cursor.execute(query, tuple(my_top_3) + (user_id,))
    peers = cursor.fetchall()
    for peer_id, match_count in peers:
        cursor.execute("""
            INSERT INTO collaborative_map (user_id, peer_id, similarity_score)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE similarity_score = %s
        """, (user_id, peer_id, match_count, match_count))
    db.commit()

def get_collaborative_discovery(user_id):
    query = """
        SELECT ui.genre 
        FROM user_interests ui
        JOIN collaborative_map cm ON ui.user_id = cm.peer_id
        WHERE cm.user_id = %s 
        AND ui.points > 100
        AND ui.genre NOT IN (
            SELECT genre FROM user_interests WHERE user_id = %s AND points > 50
        )
        ORDER BY ui.points DESC LIMIT 7
    """
    cursor.execute(query, (user_id, user_id))
    recommendations = cursor.fetchall()
    if recommendations:
        return random.choice(recommendations)[0]
    return None # Fallback to random discovery if no peers found

def get_next_blog(user_id, target_genre):
    query = """
        SELECT b.blog_id FROM ranker b
        LEFT JOIN user_history h ON b.blog_id = h.blog_id AND h.user_id = %s
        WHERE b.genre = %s AND h.blog_id IS NULL
        ORDER BY b.upload_date DESC LIMIT 1
    """
    cursor.execute(query, (user_id, target_genre))
    result = cursor.fetchone()
    if not result:
        query = """
            SELECT blog_id FROM user_history 
            WHERE user_id = %s AND genre = %s AND (is_liked = 1 OR is_saved = 1)
            ORDER BY timestamp DESC LIMIT 1
        """
        cursor.execute(query, (user_id, target_genre))
        result = cursor.fetchone()
    if not result:
        cursor.execute("SELECT blog_id FROM ranker WHERE genre = %s ORDER BY upload_date DESC LIMIT 1", (target_genre,))
        result = cursor.fetchone()  
    return result[0] if result else None

def check_blog_health(blog_id):
    cursor.execute("""
        SELECT 
            (SUM(is_liked) * 2) - (SUM(is_disliked) * 5) as health_score 
        FROM user_history 
        WHERE blog_id = %s
    """, (blog_id,))
    score = cursor.fetchone()[0] or 0
    if score < -50: # The Ghosting Threshold
        cursor.execute("UPDATE ranker SET status = 'ghosted' WHERE id = %s", (blog_id,))
        db.commit()

def log_interaction(user_id, blog_id, genre, action):
    is_l, is_d, is_s = 0, 0, 0
    if action == 'like': 
        is_l = 1
        cursor.execute("UPDATE ranker SET likes = likes + 1 WHERE id = %s", (blog_id,))
    elif action == 'dislike': 
        is_d = 1
        cursor.execute("UPDATE ranker SET dislikes = dislikes + 1 WHERE id = %s", (blog_id,))   
    elif action == 'save': 
        is_s = 1
        is_l = 1 # A save is essentially a super-like
        cursor.execute("UPDATE ranker SET saves = saves + 1, likes = likes + 1 WHERE id = %s", (blog_id,))
    new_h_id = generate_id()
    query = """
    INSERT INTO user_history (history_id, user_id, blog_id, is_liked, is_disliked, is_saved, interacted_at)
    VALUES (%s, %s, %s, %s, %s, %s, NOW())
    ON DUPLICATE KEY UPDATE
        is_liked = VALUES(is_liked),
        is_disliked = VALUES(is_disliked),
        is_saved = VALUES(is_saved),
        interacted_at = NOW()
    """
    cursor.execute(query, (new_h_id, user_id, blog_id, is_l, is_d, is_s))
    db.commit()
    
def apply_session_growth(user_id, active_genres):
    if not active_genres:
        return
    for genre in active_genres:
        cursor.execute("""
            UPDATE user_interests 
            SET points = points * 1.1 
            WHERE user_id = %s AND genre = %s
        """, (user_id, genre))
    db.commit()

def get_peer_recommendation(user_id):
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_id != %s", (user_id,))
    if cursor.fetchone()[0] == 0:
        return "SOLO_EXPLORER"
    query = """
        SELECT peer_id FROM collaborative_map 
        WHERE user_id = %s 
        ORDER BY similarity_score DESC 
        LIMIT 1
    """
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    return result[0] if result else "TRAILBLAZER"

def fetch_blog_details(blog_id):
    query = "SELECT id, filepath, genre FROM ranker WHERE id = %s"
    cursor.execute(query, (blog_id,))
    res = cursor.fetchone()
    if res:
        return {
            'id': res[0],
            'path': res[1],
            'genre': res[2]
        }
    return None

def increment_view(blog_id):
    cursor.execute("UPDATE ranker SET views = views + 1 WHERE id = %s", (blog_id,))
    db.commit()

def get_fresh_niche_blog(user_id):
    query_exclude = """
        (SELECT genre FROM user_interests WHERE user_id = %s ORDER BY points DESC LIMIT 3)
        UNION
        (SELECT genre FROM user_interests WHERE user_id = %s AND points < 0)
    """
    cursor.execute(query_exclude, (user_id, user_id))
    exclude_genres = [row[0] for row in cursor.fetchall()]
    if exclude_genres:
        placeholders = ', '.join(['%s'] * len(exclude_genres))
        query = f"""
            SELECT id, genre FROM ranker 
            WHERE genre NOT IN ({placeholders}) 
            AND status = 'Active'
            ORDER BY RAND() LIMIT 1
        """
        cursor.execute(query, tuple(exclude_genres))
    else:
        cursor.execute("SELECT id, genre FROM ranker WHERE status = 'Active' ORDER BY RAND() LIMIT 1")
    return cursor.fetchone()

def log_discovery_like(user_id, blog_id, genre):
    cursor.execute("UPDATE user_interests SET points = points + 15 WHERE user_id = %s AND genre = %s", (user_id, genre))
    cursor.execute("UPDATE ranker SET likes = likes + 5 WHERE id = %s", (blog_id,))
    db.commit()

def log_discovery_dislike(user_id, blog_id, genre):
    cursor.execute("UPDATE user_interests SET points = points - 10 WHERE user_id = %s AND genre = %s", (user_id, genre))
    cursor.execute("UPDATE ranker SET dislikes = dislikes + 0.5 WHERE id = %s", (blog_id,))
    db.commit()

def _finish_discovery_log(user_id, blog_id, is_l, is_d, is_s=0):
    new_h_id = generate_id()
    query = """
        INSERT INTO user_history (history_id, user_id, blog_id, is_liked, is_disliked, is_saved, interacted_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """
    cursor.execute(query, (new_h_id, user_id, blog_id, is_l, is_d, is_s))
    db.commit()

def discovery_mode(user_id):
    cursor.execute("SELECT genre FROM user_interests WHERE user_id = %s ORDER BY points DESC LIMIT 3", (user_id,))
    top_3 = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT genre FROM user_interests WHERE user_id = %s AND points < 0", (user_id,))
    negatives = [row[0] for row in cursor.fetchall()]
    exclude_list = top_3 if top_3 else ['_NONE_']
    placeholders = ', '.join(['%s'] * len(exclude_list))
    query = f"""
        SELECT r.id, r.genre, r.filepath 
        FROM ranker r
        LEFT JOIN user_history h ON r.id = h.blog_id AND h.user_id = %s
        WHERE r.genre NOT IN ({placeholders})
        AND r.status = 'Active'
        AND h.blog_id IS NULL
        ORDER BY (r.likes - r.dislikes) DESC
    """
    cursor.execute(query, (user_id, *exclude_list))
    candidates = cursor.fetchall()
    for b_id, b_genre, b_path in candidates: 
        if b_genre in negatives:
            continue    
        print(f"\n--- VENTURING INTO THE UNKNOWN ---")
        print(f"Bypassing your favorites to find: {b_genre}")
        return b_id, b_genre, b_path 
    return None, None, None 

def get_collaborative_content(user_id):
    peer_id = get_peer_recommendation(user_id)
    if peer_id in ["SOLO_EXPLORER", "TRAILBLAZER"]:
        return peer_id, None, None # Tell Main why we can't show a blog
    query = """
        SELECT r.id, r.genre, r.filepath 
        FROM user_history h
        JOIN ranker r ON h.blog_id = r.id
        LEFT JOIN user_history my_h ON r.id = my_h.blog_id AND my_h.user_id = %s
        WHERE h.user_id = %s 
          AND h.is_liked = 1 
          AND my_h.blog_id IS NULL
          AND r.status = 'Active'
        ORDER BY RAND() LIMIT 1
    """
    cursor.execute(query, (user_id, peer_id))
    res = cursor.fetchone()
    if res:
        return res[0], res[1], res[2] # blog_id, genre, path
    return "TRAILBLAZER", None, None

def get_discovery_blog(user_id):
    cursor.execute("SELECT genre FROM user_interests WHERE user_id = %s ORDER BY points DESC LIMIT 3", (user_id,))
    exclude_list = [row[0] for row in cursor.fetchall()] or ['_NONE_']
    cursor.execute("SELECT genre FROM user_interests WHERE user_id = %s AND points < 0", (user_id,))
    negatives = [row[0] for row in cursor.fetchall()] or ['_NONE_']
    total_exclude = list(set(exclude_list + negatives))
    placeholders = ', '.join(['%s'] * len(total_exclude))

    query = f"""
        SELECT r.id, r.genre, r.filepath 
        FROM ranker r
        LEFT JOIN user_history h ON r.id = h.blog_id AND h.user_id = %s
        WHERE r.genre NOT IN ({placeholders}) 
          AND r.status = 'Active' 
          AND h.blog_id IS NULL
        ORDER BY (r.likes - r.dislikes) DESC
        LIMIT 1
    """
    cursor.execute(query, (user_id, *total_exclude))
    result = cursor.fetchone()
    return result if result else (None, None, None)

def get_recommended_blog_v2(user_id):
    # 80/20 Logic
    chance = random.random()
    if chance < 0.80:
        # 80% - Regular Favorites
        query = """
            SELECT r.id, r.genre, r.filepath FROM ranker r
            JOIN user_interests ui ON r.genre = ui.genre
            LEFT JOIN user_history h ON r.id = h.blog_id AND h.user_id = %s
            WHERE ui.user_id = %s AND ui.points > 0 AND h.blog_id IS NULL
            ORDER BY ui.points DESC, RAND() LIMIT 1
        """
        cursor.execute(query, (user_id, user_id))
    else:
        # 20% - Random New Niche (Not top 3, not negative)
        cursor.execute("SELECT genre FROM user_interests WHERE user_id = %s ORDER BY points DESC LIMIT 3", (user_id,))
        top_3 = [row[0] for row in cursor.fetchall()] or ['_NONE_']
        
        placeholders = ', '.join(['%s'] * len(top_3))
        query = f"""
            SELECT r.id, r.genre, r.filepath FROM ranker r
            LEFT JOIN user_interests ui ON r.genre = ui.genre AND ui.user_id = %s
            LEFT JOIN user_history h ON r.id = h.blog_id AND h.user_id = %s
            WHERE (ui.points >= 0 OR ui.points IS NULL) 
            AND r.genre NOT IN ({placeholders})
            AND h.blog_id IS NULL
            ORDER BY RAND() LIMIT 1
        """
        cursor.execute(query, (user_id, user_id, *top_3))
    return cursor.fetchone() # Returns (id, genre, path) or None

def start_reading_loop(user_id, session_interests):
    while True:
        result = Engine.get_recommended_blog_v2(user_id)
        if result:
            blog_id, genre, path = result
            if not view_single_blog(user_id, blog_id, genre, session_interests, path):
                break
        else:
            print("\n[!] No blogs found matching your 80/20 criteria. Try Discovery!")
            input("Press Enter...")
            break
