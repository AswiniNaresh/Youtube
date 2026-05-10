import streamlit as st
import pandas as pd
from datetime import datetime
import traceback
import time
from googleapiclient.discovery import build
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
st.set_page_config(
    page_title="YouTube Analytics",
    page_icon="📺",
    layout="wide"
)

# Initialize session state
if 'channel_data' not in st.session_state:
    st.session_state.channel_data = None

def init_youtube_api():
    """Initialize YouTube API client"""
    api_key = "AIzaSyDhosKCf4f3RbhUNrixXPqJ41O8Mr3CODQ" #os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        st.error("YouTube API key not found! Please check your .env file.")
        return None
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        return youtube
    except Exception as e:
        st.error(f"Error initializing YouTube API: {str(e)}")
        return None

def init_database():
    """Initialize database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'admin'),
            password=os.getenv('DB_PASSWORD', '12345'),
            database=os.getenv('DB_NAME', 'youtube_data')
        )
        return connection
    except Error as e:
        st.error(f"Error connecting to database: {str(e)}")
        return None

def get_channel_stats(youtube, channel_id):
    """Fetch channel statistics"""
    try:
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=channel_id
        )
        response = request.execute()

        if not response['items']:
            st.warning(f"No channel found for ID: {channel_id}")
            return None

        channel_data = response['items'][0]
        stats = {
            'Channel Name': channel_data['snippet']['title'],
            'Subscribers': int(channel_data['statistics'].get('subscriberCount', 0)),
            'Total Videos': int(channel_data['statistics'].get('videoCount', 0)),
            'Playlist ID': channel_data['contentDetails']['relatedPlaylists']['uploads'],
            'View Count': int(channel_data['statistics'].get('viewCount', 0))
        }
        return stats
    except Exception as e:
        st.error(f"Error fetching channel stats: {str(e)}")
        return None
    
def get_video_ids(self, playlist_id, max_results=50):
        video_ids = []
        next_page_token = None

        while True:
            request = self.youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=min(50, max_results),
                pageToken=next_page_token
            )
            response = request.execute()

            video_ids.extend([item['contentDetails']['videoId'] for item in response['items']])
            next_page_token = response.get('nextPageToken')

            if not next_page_token or len(video_ids) >= max_results:
                break

        return video_ids[:max_results]

def get_video_details(self, video_id):
        try:
            video_response = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            ).execute()

            if not video_response['items']:
                return None

            video = video_response['items'][0]
            
            # Get comments if available
            comments = self.get_video_comments(video_id)

            return {
                'video_id': video_id,
                'video_name': video['snippet']['title'],
                'video_description': video['snippet']['description'],
                'published_at': datetime.strptime(
                    video['snippet']['publishedAt'], 
                    '%Y-%m-%dT%H:%M:%SZ'
                ),
                'view_count': int(video['statistics'].get('viewCount', 0)),
                'like_count': int(video['statistics'].get('likeCount', 0)),
                'dislike_count': 0,  # YouTube API no longer provides dislike counts
                'favorite_count': int(video['statistics'].get('favoriteCount', 0)),
                'comment_count': int(video['statistics'].get('commentCount', 0)),
                'duration': str(isodate.parse_duration(video['contentDetails']['duration'])),
                'thumbnail': video['snippet']['thumbnails']['default']['url'],
                'caption_status': video['contentDetails'].get('caption', 'Not Available'),
                'comments': comments
            }
        except Exception as e:
            print(f"Error fetching video details: {e}")
            return None

def get_video_comments(self, video_id, max_results=100):
        try:
            comments = []
            request = self.youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_results)
            )
            response = request.execute()

            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'comment_id': item['id'],
                    'comment_text': comment['textDisplay'],
                    'comment_author': comment['authorDisplayName'],
                    'published_at': datetime.strptime(
                        comment['publishedAt'], 
                        '%Y-%m-%dT%H:%M:%SZ'
                    )
                })

            return comments
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return []    

def main():
    st.title("YouTube Channel Analytics")
    st.write("Analyze YouTube channel data and store it in a database")

    # Initialize API
    youtube = init_youtube_api()
    if not youtube:
        st.stop()

    # Database connection
    db_conn = init_database()
    if not db_conn:
        st.warning("Database connection not available. Running in API-only mode.")

    # Input section
    with st.container():
        st.subheader("Channel Data Collection")
        channel_input = st.text_area(
            "Enter YouTube Channel IDs (one per line, max 10)",
            help="Enter up to 10 YouTube channel IDs, one per line"
        )

        if st.button("Fetch Channel Data", key="fetch_data"):
            if not channel_input.strip():
                st.warning("Please enter at least one channel ID")
                return

            channel_ids = [cid.strip() for cid in channel_input.splitlines() if cid.strip()][:10]
            
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            all_channel_data = []
            for idx, channel_id in enumerate(channel_ids):
                progress_text.write(f"Processing channel {idx + 1}/{len(channel_ids)}")
                
                stats = get_channel_stats(youtube, channel_id)
                if stats:
                    all_channel_data.append({
                        'Channel ID': channel_id,
                        **stats
                    })
                
                progress_bar.progress((idx + 1) / len(channel_ids))
                time.sleep(0.5)  # Prevent API throttling

            if all_channel_data:
                st.session_state.channel_data = pd.DataFrame(all_channel_data)
                st.success("Data collection completed!")
            else:
                st.error("No data could be collected. Please check the channel IDs.")

    # Display section
    if st.session_state.channel_data is not None:
        st.subheader("Collected Channel Data")
        st.dataframe(st.session_state.channel_data)

        # Export options
        csv = st.session_state.channel_data.to_csv(index=False)
        st.download_button(
            "Download Data as CSV",
            csv,
            "youtube_channel_data.csv",
            "text/csv",
            key='download-csv'
        )

    # Add footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>YouTube Channel Analytics Tool</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("An unexpected error occurred!")
        st.error(f"Error details: {str(e)}")
        st.error("Stack trace:")
        st.code(traceback.format_exc())
#def main():
#    st.title("YouTube Channel Analytics")
#    st.write("Analyze YouTube channel data and store it in a database")
#
#    # Initialize API
#    youtube = init_youtube_api()
#    if not youtube:
#        st.stop()
#
#    # Database connection
#    db_conn = init_database()
#    if not db_conn:
#        st.warning("Database connection not available. Running in API-only mode.")
#
#    # Input section
#    with st.container():
#        st.subheader("Channel Data Collection")
#        channel_input = st.text_area(
#            "Enter YouTube Channel IDs (one per line, max 10)",
#            help="Enter up to 10 YouTube channel IDs, one per line"
#        )
#
#        if st.button("Fetch Channel and Video Data", key="fetch_data"):
#            if not channel_input.strip():
#                st.warning("Please enter at least one channel ID")
#                return
#
#            channel_ids = [cid.strip() for cid in channel_input.splitlines() if cid.strip()][:10]
#            
#            progress_bar = st.progress(0)
#            progress_text = st.empty()
#            
#            all_channel_data = []
#            all_video_data = []
#            all_comments_data = []
#
#            for idx, channel_id in enumerate(channel_ids):
#                progress_text.write(f"Processing channel {idx + 1}/{len(channel_ids)}")
#
#                # Fetch channel stats
#                stats = get_channel_stats(youtube, channel_id)
#                if stats:
#                    all_channel_data.append({
#                        'Channel ID': channel_id,
#                        **stats
#                    })
#
#                # Fetch video IDs
#                playlist_id = stats.get('Playlist ID')
#                if playlist_id:
#                    video_ids = get_video_ids(youtube, playlist_id)
#                    for video_id in video_ids:
#                        # Fetch video details
#                        video_details = get_video_details(youtube, video_id)
#                        if video_details:
#                            all_video_data.append({
#                                "Channel Name": stats["Channel Name"],
#                                **video_details
#                            })
#                        
#                        # Fetch video comments
#                        comments = get_video_comments(youtube, video_id)
#                        for comment in comments:
#                            all_comments_data.append({
#                                "Video ID": video_id,
#                                **comment
#                            })
#
#                progress_bar.progress((idx + 1) / len(channel_ids))
#                time.sleep(0.5)  # Prevent API throttling
#
#            # Save data to session state
#            if all_channel_data:
#                st.session_state.channel_data = pd.DataFrame(all_channel_data)
#            if all_video_data:
#                st.session_state.video_data = pd.DataFrame(all_video_data)
#            if all_comments_data:
#                st.session_state.comments_data = pd.DataFrame(all_comments_data)
#
#            st.success("Data collection completed!")
#        else:
#            st.error("No data could be collected. Please check the channel IDs.")
#
#    # Display collected data
#    if st.session_state.get("channel_data") is not None:
#        st.subheader("Collected Channel Data")
#        st.dataframe(st.session_state.channel_data)
#
#    if st.session_state.get("video_data") is not None:
#        st.subheader("Collected Video Data")
#        st.dataframe(st.session_state.video_data)
#
#    if st.session_state.get("comments_data") is not None:
#        st.subheader("Collected Comments Data")
#        st.dataframe(st.session_state.comments_data)
#
#    # Export options for channel, video, and comment data
#    if st.session_state.get("channel_data") is not None:
#        csv_channel = st.session_state.channel_data.to_csv(index=False)
#        st.download_button(
#            "Download Channel Data as CSV",
#            csv_channel,
#            "youtube_channel_data.csv",
#            "text/csv",
#            key='download-channel-csv'
#        )
#
#    if st.session_state.get("video_data") is not None:
#        csv_video = st.session_state.video_data.to_csv(index=False)
#        st.download_button(
#            "Download Video Data as CSV",
#            csv_video,
#            "youtube_video_data.csv",
#            "text/csv",
#            key='download-video-csv'
#        )
#
#    if st.session_state.get("comments_data") is not None:
#        csv_comments = st.session_state.comments_data.to_csv(index=False)
#        st.download_button(
#            "Download Comments Data as CSV",
#            csv_comments,
#            "youtube_comments_data.csv",
#            "text/csv",
#            key='download-comments-csv'
#        )
#
#    # Add footer
#    st.markdown("---")
#    st.markdown(
#        """
#        <div style='text-align: center'>
#            <p>YouTube Channel Analytics Tool</p>
#        </div>
#        """,
#        unsafe_allow_html=True
#    )
#
#if __name__ == "__main__":
#    try:
#        main()
#    except Exception as e:
#        st.error("An unexpected error occurred!")
#        st.error(f"Error details: {str(e)}")
#        st.error("Stack trace:")
#        st.code(traceback.format_exc())
