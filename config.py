import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv('AIzaSyDhosKCf4f3RbhUNrixXPqJ41O8Mr3CODQ')
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'admin'),
    'password': os.getenv('DB_PASSWORD', '12345'),
    'database': os.getenv('DB_NAME', 'youtube_data')
}

grok_api_key = value ("")