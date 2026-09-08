import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

video_id = "dQw4w9WgXcQ"

url = "https://www.googleapis.com/youtube/v3/commentThreads"

params = {
    "part": "snippet",
    "videoId": video_id,
    "key": API_KEY,
    "maxResults": 10
}

response = requests.get(url, params=params)

print("Status:", response.status_code)
print(response.json())
