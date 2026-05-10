import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import isodate

# Configure page
st.set_page_config(page_title="YouTube Channel Analyzer", layout="wide")

# Initialize session states
if 'channels_data' not in st.session_state:
    st.session_state.channels_data = []

# MySQL Configuration
def create_server_connection():
    try:
        connection = mysql.connector.connect(
            host=st.secrets["mysql_host"],
            user=st.secrets["mysql_user"],
            password=st.secrets["mysql_password"],
            database=st.secrets["mysql_database"]
        )
        return connection
    except Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None

def create_database_tables(connection):
    try:
        cursor = connection.cursor()
        
        # Create channels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id VARCHAR(255) PRIMARY KEY,
                channel_name VARCHAR(255),
                subscribers INT,
                total_views BIGINT,
                description TEXT,
                playlist_id VARCHAR(255)
            )
        """)
        
        # Create videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id VARCHAR(255) PRIMARY KEY,
                channel_id VARCHAR(255),
                title VARCHAR(255),
                description TEXT,
                published_date DATETIME,
                views BIGINT,
                likes INT,
                comment_count INT,
                duration VARCHAR(255),
                thumbnail VARCHAR(255),
                FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
            )
        """)
        
        # Create comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                comment_id VARCHAR(255) PRIMARY KEY,
                video_id VARCHAR(255),
                comment_text TEXT,
                author VARCHAR(255),
                published_date DATETIME,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        """)
        
        connection.commit()
    except Error as e:
        st.error(f"Error creating tables: {e}")

# YouTube API functions remain the same as previous version

def store_data_in_mysql(connection, channel_data):
    try:
        cursor = connection.cursor()
        
        # Insert channel data
        channel_query = """
            INSERT INTO channels (channel_id, channel_name, subscribers, total_views, description, playlist_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            channel_name=VALUES(channel_name),
            subscribers=VALUES(subscribers),
            total_views=VALUES(total_views),
            description=VALUES(description),
            playlist_id=VALUES(playlist_id)
        """
        channel_values = (
            channel_data['Channel_Id'],
            channel_data['Channel_Name'],
            channel_data['Subscription_Count'],
            channel_data['Channel_Views'],
            channel_data['Channel_Description'],
            channel_data['Playlist_Id']
        )
        cursor.execute(channel_query, channel_values)

        # Insert videos data
        for video_id, video in channel_data['Videos'].items():
            video_query = """
                INSERT INTO videos (video_id, channel_id, title, description, published_date,
                                  views, likes, comment_count, duration, thumbnail)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                title=VALUES(title),
                description=VALUES(description),
                views=VALUES(views),
                likes=VALUES(likes),
                comment_count=VALUES(comment_count)
            """
            video_values = (
                video_id,
                channel_data['Channel_Id'],
                video['Video_Name'],
                video['Video_Description'],
                video['PublishedAt'],
                video['View_Count'],
                video['Like_Count'],
                video['Comment_Count'],
                video['Duration'],
                video['Thumbnail']
            )
            cursor.execute(video_query, video_values)

            # Insert comments data
            for comment_id, comment in video['Comments'].items():
                comment_query = """
                    INSERT INTO comments (comment_id, video_id, comment_text, author, published_date)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    comment_text=VALUES(comment_text),
                    author=VALUES(author),
                    published_date=VALUES(published_date)
                """
                comment_values = (
                    comment_id,
                    video_id,
                    comment['Comment_Text'],
                    comment['Comment_Author'],
                    comment['Comment_PublishedAt']
                )
                cursor.execute(comment_query, comment_values)

        connection.commit()
        return True
    except Error as e:
        st.error(f"Error storing data in MySQL: {e}")
        return False

def execute_query(connection, query):
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        return pd.DataFrame(results, columns=columns)
    except Error as e:
        st.error(f"Error executing query: {e}")
        return None

def get_analysis_queries():
    queries = {
        "Video and Channel Names": """
            SELECT v.title as video_name, c.channel_name
            FROM videos v
            JOIN channels c ON v.channel_id = c.channel_id
            ORDER BY c.channel_name, v.title
        """,
        
        "Channels with Most Videos": """
            SELECT c.channel_name, COUNT(v.video_id) as video_count
            FROM channels c
            LEFT JOIN videos v ON c.channel_id = v.channel_id
            GROUP BY c.channel_name
            ORDER BY video_count DESC
        """,
        
        "Top 10 Most Viewed Videos": """
            SELECT v.title, c.channel_name, v.views
            FROM videos v
            JOIN channels c ON v.channel_id = c.channel_id
            ORDER BY v.views DESC
            LIMIT 10
        """,
        
        "Comments per Video": """
            SELECT v.title, COUNT(cm.comment_id) as comment_count
            FROM videos v
            LEFT JOIN comments cm ON v.video_id = cm.video_id
            GROUP BY v.title
            ORDER BY comment_count DESC
        """,
        
        "Most Liked Videos": """
            SELECT v.title, c.channel_name, v.likes
            FROM videos v
            JOIN channels c ON v.channel_id = c.channel_id
            ORDER BY v.likes DESC
            LIMIT 10
        """,
        
        "Total Views per Channel": """
            SELECT channel_name, total_views
            FROM channels
            ORDER BY total_views DESC
        """,
        
        "Channels with 2022 Videos": """
            SELECT DISTINCT c.channel_name
            FROM channels c
            JOIN videos v ON c.channel_id = v.channel_id
            WHERE YEAR(v.published_date) = 2022
            ORDER BY c.channel_name
        """,
        
        "Average Video Duration by Channel": """
            SELECT 
                c.channel_name,
                AVG(
                    TIME_TO_SEC(
                        CONCAT(
                            SUBSTRING_INDEX(
                                SUBSTRING_INDEX(v.duration, 'H', 1),
                                'PT',
                                -1
                            ),
                            ':',
                            SUBSTRING_INDEX(
                                SUBSTRING_INDEX(v.duration, 'M', 1),
                                'H',
                                -1
                            ),
                            ':',
                            SUBSTRING_INDEX(
                                SUBSTRING_INDEX(v.duration, 'S', 1),
                                'M',
                                -1
                            )
                        )
                    )
                ) as avg_duration_seconds
            FROM channels c
            JOIN videos v ON c.channel_id = v.channel_id
            GROUP BY c.channel_name
            ORDER BY avg_duration_seconds DESC
        """,
        
        "Most Commented Videos": """
            SELECT v.title, c.channel_name, v.comment_count
            FROM videos v
            JOIN channels c ON v.channel_id = c.channel_id
            ORDER BY v.comment_count DESC
            LIMIT 10
        """
    }
    return queries

def main():
    st.title("YouTube Channel Analyzer")

    # Database connection
    connection = create_server_connection()
    if connection:
        create_database_tables(connection)
    else:
        st.error("Failed to connect to database")
        return

    # Sidebar inputs
    with st.sidebar:
        st.header("Channel Input")
        channel_id = st.text_input("Enter YouTube Channel ID")
        fetch_button = st.button("Fetch Channel Data")
        
        st.header("Data Storage")
        store_button = st.button("Store in Database")
        
        st.header("Data Analysis")
        queries = get_analysis_queries()
        analysis_option = st.selectbox(
            "Select Analysis Type",
            list(queries.keys())
        )

    # Main content
    if fetch_button and channel_id:
        youtube = get_youtube_client()
        with st.spinner("Fetching channel data..."):
            channel_data = get_channel_data(youtube, channel_id)
            if channel_data:
                st.session_state.channels_data.append(channel_data)
                st.success("Channel data fetched successfully!")
            else:
                st.error("Failed to fetch channel data.")

    if store_button and st.session_state.channels_data:
        with st.spinner("Storing data in database..."):
            success = all(store_data_in_mysql(connection, data) 
                         for data in st.session_state.channels_data)
            if success:
                st.success("Data stored successfully!")
                st.session_state.channels_data = []
            else:
                st.error("Failed to store some data.")

    # Display query results
    if analysis_option:
        st.header(analysis_option)
        query = queries[analysis_option]
        results = execute_query(connection, query)
        if results is not None:
            st.dataframe(results)

if __name__ == "__main__":
    main()