ANALYSIS_QUERIES = {
    "videos_and_channels": """
        SELECT v.video_name, c.channel_name 
        FROM videos v 
        JOIN channels c ON v.channel_id = c.channel_id
    """,
    
    "channels_by_videos": """
        SELECT c.channel_name, COUNT(v.video_id) as video_count 
        FROM channels c 
        LEFT JOIN videos v ON c.channel_id = v.channel_id 
        GROUP BY c.channel_id, c.channel_name 
        ORDER BY video_count DESC
    """,
    
    "top_viewed_videos": """
        SELECT v.video_name, c.channel_name, v.view_count 
        FROM videos v 
        JOIN channels c ON v.channel_id = c.channel_id 
        ORDER BY v.view_count DESC 
        LIMIT 10
    """,
    
    "comments_by_video": """
        SELECT v.video_name, COUNT(cm.comment_id) as comment_count 
        FROM videos v 
        LEFT JOIN comments cm ON v.video_id = cm.video_id 
        GROUP BY v.video_id, v.video_name 
        ORDER BY comment_count DESC
    """,
    
    "most_liked_videos": """
        SELECT v.video_name, c.channel_name, v.like_count 
        FROM videos v 
        JOIN channels c ON v.channel_id = c.channel_id 
        ORDER BY v.like_count DESC 
        LIMIT 10
    """,
    
    "likes_by_video": """
        SELECT v.video_name, v.like_count, v.dislike_count 
        FROM videos v 
        ORDER BY v.like_count DESC
    """,
    
    "views_by_channel": """
        SELECT c.channel_name, SUM(v.view_count) as total_views 
        FROM channels c 
        LEFT JOIN videos v ON c.channel_id = v.channel_id 
        GROUP BY c.channel_id, c.channel_name 
        ORDER BY total_views DESC
    """,
    
    "videos_2022": """
        SELECT DISTINCT c.channel_name 
        FROM channels c 
        JOIN videos v ON c.channel_id = v.channel_id 
        WHERE YEAR(v.published_at) = 2022
    """,
    
    "avg_duration": """
        SELECT 
            c.channel_name,
            SEC_TO_TIME(AVG(TIME_TO_SEC(TIME(v.duration)))) as avg_duration
        FROM channels c 
        JOIN videos v ON c.channel_id = v.channel_id 
        GROUP BY c.channel_id, c.channel_name
    """,
    
    "most_commented_videos": """
        SELECT v.video_name, c.channel_name, v.comment_count 
        FROM videos v 
        JOIN channels c ON v.channel_id = c.channel_id 
        ORDER BY v.comment_count DESC 
        LIMIT 10
    """
}