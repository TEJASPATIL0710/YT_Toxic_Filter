"""
livechat_fetcher.py

Fetches messages from an active YouTube live stream's chat, using the
YouTube Data API v3 `liveChatMessages.list` endpoint.

Unlike VodFetcher, this needs an extra lookup first: given a live
video's ID, we have to ask the API for that video's `liveChatId`
before we can poll for messages.

Usage:
    fetcher = LiveChatFetcher(video_id="the_live_stream_video_id")
    while fetcher.has_more():
        for comment in fetcher.fetch_batch():
            handle(comment)
        time.sleep(fetcher.poll_delay_seconds())
"""

import os
from typing import Iterator, Optional

from googleapiclient.discovery import build

from fetcher.base import Comment, CommentFetcher


class LiveChatFetcher(CommentFetcher):
    def __init__(self, video_id: str, api_key: Optional[str] = None):
        self.video_id = video_id
        key = api_key or os.environ.get("YT_API_KEY")
        if not key:
            raise ValueError(
                "No API key found. Pass api_key= or set the YT_API_KEY "
                "environment variable."
            )
        self._youtube = build("youtube", "v3", developerKey=key)
        self._live_chat_id = self._resolve_live_chat_id()
        self._next_page_token: Optional[str] = None
        self._last_poll_delay_ms: float = 5000  # sensible default before first poll
        self._stream_ended = False

    def _resolve_live_chat_id(self) -> str:
        """
        Looks up the liveChatId associated with this video. Raises if the
        video isn't currently live (or never was).
        """
        response = self._youtube.videos().list(
            part="liveStreamingDetails", id=self.video_id
        ).execute()
        items = response.get("items", [])
        if not items:
            raise ValueError(f"No video found for id={self.video_id}")

        details = items[0].get("liveStreamingDetails", {})
        live_chat_id = details.get("activeLiveChatId")
        if not live_chat_id:
            raise ValueError(
                f"Video {self.video_id} has no active live chat "
                "(it may not be currently live)."
            )
        return live_chat_id

    def fetch_batch(self) -> Iterator[Comment]:
        if self._stream_ended:
            return

        response = self._youtube.liveChatMessages().list(
            liveChatId=self._live_chat_id,
            part="snippet,authorDetails",
            pageToken=self._next_page_token,
        ).execute()

        for item in response.get("items", []):
            snippet = item["snippet"]
            author = item.get("authorDetails", {})
            yield Comment(
                comment_id=item["id"],
                video_id=self.video_id,
                author=author.get("displayName", "unknown"),
                text=snippet.get("displayMessage", ""),
                published_at=snippet.get("publishedAt", ""),
                source="live",
            )

        self._next_page_token = response.get("nextPageToken")
        # The API returns this so we don't poll faster than it wants us to.
        self._last_poll_delay_ms = response.get("pollingIntervalMillis", 5000)

        if response.get("offlineAt"):
            # Stream has ended.
            self._stream_ended = True

    def has_more(self) -> bool:
        return not self._stream_ended

    def poll_delay_seconds(self) -> Optional[float]:
        return self._last_poll_delay_ms / 1000
