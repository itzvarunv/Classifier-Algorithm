#Excess
def get_recommended_blog(user_id):
    cursor.execute("""
        SELECT genre FROM user_interests 
        WHERE user_id = %s AND points >= 45 
        ORDER BY points DESC, RAND() LIMIT 5
    """, (user_id,))
    
    potential_genres = [row[0] for row in cursor.fetchall()]
    for target_genre in potential_genres:
        query = """
            SELECT b.id FROM ranker b
            LEFT JOIN user_history h ON b.id = h.blog_id AND h.user_id = %s
            WHERE b.genre = %s AND b.status = 'Active' AND h.blog_id IS NULL
            LIMIT 1
        """
        cursor.execute(query, (user_id, target_genre))
        if cursor.fetchone():
            return target_genre # Found one with actual content!        
    return None # Truly exhausted all interests

def get_discovery_genre(user_id):
    query = """
        SELECT ui.genre 
        FROM user_interests ui
        JOIN ranker r ON ui.genre = r.genre
        LEFT JOIN user_history h ON r.id = h.blog_id AND h.user_id = %s
        WHERE ui.user_id = %s 
          AND ui.points BETWEEN 45 AND 55
          AND r.status = 'Active'
          AND h.blog_id IS NULL
        GROUP BY ui.genre
        ORDER BY RAND() 
        LIMIT 1
    """
    cursor.execute(query, (user_id, user_id))
    res = cursor.fetchone()
    return res[0] if res else None

def get_balanced_blog(user_id, target_genre):
    query = """
        SELECT b.id AS blog_id, b.likes 
        FROM ranker b
        LEFT JOIN user_history h ON b.id = h.blog_id AND h.user_id = %s
        WHERE b.genre = %s 
        AND b.status = 'Active'
        AND h.blog_id IS NULL
        ORDER BY b.likes DESC 
        LIMIT 10
    """
    cursor.execute(query, (user_id, target_genre))
    candidates = cursor.fetchall()
    if candidates:
        if random.random() > 0.2:
            return candidates[0][0] 
        else:
            return random.choice(candidates[1:])[0] if len(candidates) > 1 else candidates[0][0]
    return None

