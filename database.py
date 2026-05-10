import mysql.connector
from mysql.connector import Error
import pandas as pd
from config import DB_CONFIG
from schemas import CHANNEL_TABLE, VIDEO_TABLE, COMMENT_TABLE

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
        except Error as e:
            print(f"Database connection error: {e}")

    def create_tables(self):
        try:
            cursor = self.connection.cursor()
            cursor.execute(CHANNEL_TABLE)
            cursor.execute(VIDEO_TABLE)
            cursor.execute(COMMENT_TABLE)
            self.connection.commit()
        except Error as e:
            print(f"Error creating tables: {e}")

    def insert_channel(self, channel_data):
        query = """
        INSERT INTO channels 
        (channel_id, channel_name, subscription_count, channel_views, 
         channel_description, playlist_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        channel_name=VALUES(channel_name),
        subscription_count=VALUES(subscription_count),
        channel_views=VALUES(channel_views)
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(channel_data.values()))
            self.connection.commit()
        except Error as e:
            print(f"Error inserting channel: {e}")

    def insert_video(self, video_data, channel_id):
        query = """
        INSERT INTO videos 
        (video_id, channel_id, video_name, video_description, published_at,
         view_count, like_count, dislike_count, favorite_count, comment_count,
         duration, thumbnail, caption_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        view_count=VALUES(view_count),
        like_count=VALUES(like_count),
        comment_count=VALUES(comment_count)
        """
        try:
            cursor = self.connection.cursor()
            values = (
                video_data['video_id'],
                channel_id,
                video_data['video_name'],
                video_data['video_description'],
                video_data['published_at'],
                video_data['view_count'],
                video_data['like_count'],
                video_data['dislike_count'],
                video_data['favorite_count'],
                video_data['comment_count'],
                video_data['duration'],
                video_data['thumbnail'],
                video_data['caption_status']
            )
            cursor.execute(query, values)
            self.connection.commit()

            # Insert comments
            if video_data['comments']:
                self.insert_comments(video_data['comments'], video_data['video_id'])
        except Error as e:
            print(f"Error inserting video: {e}")

    def insert_comments(self, comments, video_id):
        query = """
        INSERT INTO comments 
        (comment_id, video_id, comment_text, comment_author, published_at)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        comment_text=VALUES(comment_text)
        """
        try:
            cursor = self.connection.cursor()
            for comment in comments:
                values = (
                    comment['comment_id'],
                    video_id,
                    comment['comment_text'],
                    comment['comment_author'],
                    comment['published_at']
                )
                cursor.execute(query, values)
            self.connection.commit()
        except Error as e:
            print(f"Error inserting comments: {e}")

    def execute_query(self, query):
        try:
            return pd.read_sql_query(query, self.connection)
        except Error as e:
            print(f"Error executing query: {e}")
            return None