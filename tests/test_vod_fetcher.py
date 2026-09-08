"""
test_vod_fetcher.py

We mock the YouTube API client entirely here -- these tests don't make
real network calls. That's intentional: unit tests should run fast, for
free, and without needing a real API key. Save real API testing for a
manual smoke-test script (see scripts/smoke_test.py, added in a later
sprint) that you run occasionally with a live key.
"""

from unittest.mock import MagicMock, patch

from fetcher.vod_fetcher import VodFetcher


FAKE_API_RESPONSE = {
    "items": [
        {
            "snippet": {
                "topLevelComment": {
                    "id": "abc123",
                    "snippet": {
                        "authorDisplayName": "Test User",
                        "textDisplay": "This is a normal comment",
                        "publishedAt": "2026-01-01T00:00:00Z",
                    },
                }
            }
        }
    ],
    "nextPageToken": None,
}


@patch("fetcher.vod_fetcher.build")
def test_fetch_batch_yields_comments(mock_build):
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    mock_youtube.commentThreads().list().execute.return_value = FAKE_API_RESPONSE

    fetcher = VodFetcher(video_id="dummy_video_id", api_key="dummy_key")
    comments = list(fetcher.fetch_batch())

    assert len(comments) == 1
    assert comments[0].text == "This is a normal comment"
    assert comments[0].source == "vod"
    assert comments[0].video_id == "dummy_video_id"


@patch("fetcher.vod_fetcher.build")
def test_has_more_becomes_false_when_no_next_page(mock_build):
    mock_youtube = MagicMock()
    mock_build.return_value = mock_youtube
    mock_youtube.commentThreads().list().execute.return_value = FAKE_API_RESPONSE

    fetcher = VodFetcher(video_id="dummy_video_id", api_key="dummy_key")
    list(fetcher.fetch_batch())  # consume the one page

    assert fetcher.has_more() is False


@patch("fetcher.vod_fetcher.build")
def test_missing_api_key_raises(mock_build):
    import pytest

    with pytest.raises(ValueError):
        VodFetcher(video_id="dummy_video_id", api_key=None)
