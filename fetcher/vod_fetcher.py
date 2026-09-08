"""
vod_fetcher.py

Fetches comments from a regular (non-live) YouTube video using the
YouTube Data API v3 `commentThreads.list` endpoint.

Setup required before this will run:
1. Go to https://console.cloud.google.com/ and create a project (or use
   an existing one).
2. Enable "YouTube Data API v3" under APIs & Services > Library.
3. Create an API key under APIs & Services > Credentials.
4. Set it as an environment variable so it's never hardcoded in source:
       export YT_API_KEY="your-key-here"      (Linux/macOS)
       setx YT_API_KEY "your-key-here"         (Windows)
   Never commit the raw key to git -- add a .env file to .gitignore if you
   use one.
"""

import os
from typing import Iterator, Optional

from googleapiclient.discovery import build

from fetcher.base import Comment, CommentFetcher


class VodFetcher(CommentFetcher):
    def __init__(self, video_id: str, api_key: Optional[str] = None, page_size: int = 100):
        """
        video_id: the 11-character YouTube video ID (the part after
                  "v=" in a normal youtube.com/watch?v=... URL)
        api_key:  falls back to the YT_API_KEY environment variable if
                  not passed explicitly
        page_size: how many comments to request per API call (max 100)
        """
        self.video_id = video_id
        key = api_key or os.environ.get("YT_API_KEY")
        if not key:
            raise ValueError(
                "No API key found. Pass api_key= or set the YT_API_KEY "
                "environment variable."
            )
        self._youtube = build("youtube", "v3", developerKey=key)
        self._page_size = page_size
        self._next_page_token: Optional[str] = None
        self._exhausted = False

    def fetch_batch(self) -> Iterator[Comment]:
        """
        Fetches one page (up to page_size) of top-level comments and their
        replies for self.video_id, then advances the internal page token
        for the next call.
        """
        if self._exhausted:
            return

        request = self._youtube.commentThreads().list(
            part="snippet",
            videoId=self.video_id,
            maxResults=self._page_size,
            pageToken=self._next_page_token,
            textFormat="plainText",
        )
        response = request.execute()

        for item in response.get("items", []):
            top_level = item["snippet"]["topLevelComment"]["snippet"]
            yield Comment(
                comment_id=item["snippet"]["topLevelComment"]["id"],
                video_id=self.video_id,
                author=top_level.get("authorDisplayName", "unknown"),
                text=top_level.get("textDisplay", ""),
                published_at=top_level.get("publishedAt", ""),
                source="vod",
            )

        self._next_page_token = response.get("nextPageToken")
        if self._next_page_token is None:
            self._exhausted = True

    def has_more(self) -> bool:
        return not self._exhausted

    def poll_delay_seconds(self) -> Optional[float]:
        # No polling delay needed for VOD -- pages can be fetched
        # back-to-back (subject to your daily quota).
        return None
