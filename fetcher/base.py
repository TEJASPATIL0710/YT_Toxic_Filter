"""
base.py

Defines the shared interface every comment source (regular video comments,
live stream chat) must implement. The pipeline code only ever talks to this
interface -- it never needs to know whether a comment came from a VOD or a
live stream.

Why this matters: without this abstraction, you'd end up writing two
separate copies of your classify/decide logic (one for VOD, one for live).
By making both fetchers return the same shape of data, the rest of the
pipeline (classifier, decision layer, dashboard) can stay a single
codebase.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass
class Comment:
    """
    A single comment/chat message, normalized to a common shape regardless
    of whether it came from a video's comment section or a live chat.

    Fields:
        comment_id: Unique ID from YouTube (comment ID or live chat message ID)
        video_id: The video (or livestream) this comment belongs to
        author: Display name of the commenter
        text: The raw comment text
        published_at: ISO 8601 timestamp string from the API
        source: "vod" or "live" -- lets downstream code log/filter by source
                if it ever needs to, without needing two data models
    """
    comment_id: str
    video_id: str
    author: str
    text: str
    published_at: str
    source: str  # "vod" or "live"


class CommentFetcher(ABC):
    """
    Abstract base class for anything that can produce a stream of Comment
    objects. VodFetcher and LiveChatFetcher will both subclass this.
    """

    @abstractmethod
    def fetch_batch(self) -> Iterator[Comment]:
        """
        Fetch the next available batch of comments.

        For VOD: this typically means "the next page of results."
        For live chat: this means "whatever new messages have arrived
        since the last poll."

        Implementations should yield Comment objects one at a time so the
        pipeline can start processing before the whole batch is downloaded.
        """
        raise NotImplementedError

    @abstractmethod
    def has_more(self) -> bool:
        """
        Whether calling fetch_batch() again makes sense right now.

        For VOD: False once you've paginated through all comments.
        For live chat: effectively always True while the stream is live
        (there's always a "next" poll to do).
        """
        raise NotImplementedError

    @abstractmethod
    def poll_delay_seconds(self) -> Optional[float]:
        """
        How long the pipeline should wait before calling fetch_batch()
        again.

        For VOD: None (no delay needed -- pages can be fetched back-to-back
        up to your quota limits).
        For live chat: a number of seconds, taken from the API's
        recommended pollingIntervalMillis, so we don't hammer the endpoint
        or burn through quota needlessly.
        """
        raise NotImplementedError
