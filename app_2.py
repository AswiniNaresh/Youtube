import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
import time
from database import Database  # Assuming you have a database module
from queries import ANALYSIS_QUERIES  # Assuming you have predefined analysis queries
from config import YOUTUBE_API_KEY  # Ensure your YouTube API key is in this file

# YouTubeAPI Class
class YouTubeAPI:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_channel_details(self, channel_id):
        request = self.youtube.channels().list(part="snippet,statistics,contentDetails", id=channel_id)
        response = request.execute()
        if "items" not in response or not response["items"]:
            return None
        item = response["items"][0]
        return {
            "channel_id": channel_id,
            "channel_name": item["snippet"]["title"],
            "playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
            "subscribers": item["statistics"].get("subscriberCount", 0),
            "video_count": item["statistics"].get("videoCount", 0),
        }

    def get_video_ids(self, playlist_id):
        video_ids = []
        request = self.youtube.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=50)
        while request:
            response = request.execute()
            video_ids.extend([item["snippet"]["resourceId"]["videoId"] for item in response["items"]])
            request = self.youtube.playlistItems().list_next(request, response)
        return video_ids

    def get_video_details(self, video_id):
        request = self.youtube.videos().list(part="snippet,statistics", id=video_id)
        response = request.execute()
        if "items" not in response or not response["items"]:
            return None
        item = response["items"][0]
        return {
            "video_id": video_id,
            "video_name": item["snippet"]["title"],
            "video_description": item["snippet"]["description"],
            "view_count": item["statistics"].get("viewCount", 0),
            "like_count": item["statistics"].get("likeCount", 0),
            "dislike_count": item["statistics"].get("dislikeCount", 0),
            "comment_count": item["statistics"].get("commentCount", 0),
            "published_at": item["snippet"]["publishedAt"],
        }

    def get_video_comments(self, video_id):
        comments = []
        request = self.youtube.commentThreads().list(part="snippet", videoId=video_id, textFormat="plainText")
        while request:
            response = request.execute()
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "comment_id": item["id"],
                    "comment_text": comment["textDisplay"],
                    "comment_author": comment["authorDisplayName"],
                    "comment_publishedAt": comment["publishedAt"],
                })
            request = self.youtube.commentThreads().list_next(request, response)
        return comments

# Database Class (simplified)
class Database:
    def insert_channel(self, channel_data):
        # Insert channel data into your database (e.g., MySQL, PostgreSQL)
        pass

    def insert_video(self, video_data, channel_id):
        # Insert video data into the database
        pass

    def execute_query(self, query):
        # Execute an SQL query and return results as a pandas DataFrame
        return pd.DataFrame()  # Replace with actual database query logic

def main():
    st.title("YouTube Channel Analytics")
    st.write("Analyze YouTube channel data and store it in a database.")

    # Initialize YouTube API
    try:
        yt_api = YouTubeAPI("AIzaSyDhosKCf4f3RbhUNrixXPqJ41O8Mr3CODQ")  # Ensure YOUTUBE_API_KEY is properly imported and valid
        if not isinstance(yt_api, YouTubeAPI):  # Verify yt_api is a YouTubeAPI object
            raise TypeError("YouTubeAPI initialization failed.")
        st.success("YouTube API initialized successfully.")
    except Exception as e:
        st.error(f"Failed to initialize YouTube API: {str(e)}")
        return

    # Initialize Database
    db = Database()

    # Channel input section
    st.header("Channel Data Collection")
    channel_ids = st.text_area(
        "Enter YouTube Channel IDs (one per line, max 10)",
        height=150
    )

    if st.button("Fetch Channel Data"):
        channel_list = channel_ids.strip().split('\n')[:10]
        
        with st.spinner("Fetching data..."):
            for channel_id in channel_list:
                channel_id = channel_id.strip()
                if not channel_id:
                    continue
                
                # Get channel details
                channel_data = yt_api.get_channel_details(channel_id)
                if not channel_data:
                    st.error(f"Could not fetch data for channel ID: {channel_id}")
                    continue
                
                # Store channel data
                db.insert_channel(channel_data)
                
                # Get video IDs
                video_ids = yt_api.get_video_ids(channel_data['playlist_id'])
                
                # Get and store video details
                for video_id in video_ids:
                    video_data = yt_api.get_video_details(video_id)
                    if video_data:
                        db.insert_video(video_data, channel_id)
                
                st.success(f"Data collected for channel: {channel_data['channel_name']}")

    # Analysis section
    st.header("Data Analysis")
    analysis_option = st.selectbox(
        "Select Analysis",
        list(ANALYSIS_QUERIES.keys())
    )

    if analysis_option:
        results = db.execute_query(ANALYSIS_QUERIES[analysis_option])
        if results is not None and not results.empty:
            st.dataframe(results)

            # Download button
            csv = results.to_csv(index=False)
            st.download_button(
                "Download Results",
                csv,
                f"{analysis_option}.csv",
                "text/csv",
                key=f'download_{analysis_option}'
            )
        else:
            st.warning("No results found for the selected analysis.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("An unexpected error occurred!")
        st.error(f"Error details: {str(e)}")
