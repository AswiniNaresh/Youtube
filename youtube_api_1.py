from googleapiclient.discovery import build
from datetime import datetime
import isodate

class YouTubeAPI:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_channel_details(self, channel_id):
        try:
            request = self.youtube.channels().list(
                part="snippet,contentDetails,statistics",
                id=channel_id
            )
            response = request.execute()

            if not response['items']:
                return None

            channel = response['items'][0]
            return {
                'channel_id': channel_id,
                'channel_name': channel['snippet']['title'],
                'subscription_count': int(channel['statistics'].get('subscriberCount', 0)),
                'channel_views': int(channel['statistics'].get('viewCount', 0)),
                'channel_description': channel['snippet']['description'],
                'playlist_id': channel['contentDetails']['relatedPlaylists']['uploads'],
                'created_at': datetime.now()
            }
        except Exception as e:
            print(f"Error fetching channel details: {e}")
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