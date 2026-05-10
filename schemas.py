CHANNEL_TABLE = """
CREATE TABLE IF NOT EXISTS channels (
    channel_id VARCHAR(255) PRIMARY KEY,
    channel_name VARCHAR(255),
    subscription_count INT,
    channel_views BIGINT,
    channel_description TEXT,
    playlist_id VARCHAR(255),
    created_at DATETIME
)
"""

VIDEO_TABLE = """
CREATE TABLE IF NOT EXISTS videos (
    video_id VARCHAR(255) PRIMARY KEY,
    channel_id VARCHAR(255),
    video_name VARCHAR(255),
    video_description TEXT,
    published_at DATETIME,
    view_count BIGINT,
    like_count INT,
    dislike_count INT,
    favorite_count INT,
    comment_count INT,
    duration VARCHAR(20),
    thumbnail VARCHAR(255),
    caption_status VARCHAR(50),
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
)
"""

COMMENT_TABLE = """
CREATE TABLE IF NOT EXISTS comments (
    comment_id VARCHAR(255) PRIMARY KEY,
    video_id VARCHAR(255),
    comment_text TEXT,
    comment_author VARCHAR(255),
    published_at DATETIME,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
)"""