from googleapiclient.discovery import build

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
        request = self.youtube.playlistItems().list(part="contentDetails", playlistId=playlist_id, maxResults=50)
        while request:
            response = request.execute()
            video_ids.extend(item["contentDetails"]["videoId"] for item in response["items"])
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
            "title": item["snippet"]["title"],
            "views": item["statistics"].get("viewCount", 0),
            "likes": item["statistics"].get("likeCount", 0),
            "comments": item["statistics"].get("commentCount", 0),
        }
    
    def get_video_comments(self, video_id):
        comments = []
        request = self.youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=50)
        while request:
            response = request.execute()
            comments.extend({
                "comment_id": item["id"],
                "text": item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
            } for item in response["items"])
            request = self.youtube.commentThreads().list_next(request, response)
        return comments
