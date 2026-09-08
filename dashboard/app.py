"""
app.py (dashboard)

Run with:
    streamlit run dashboard/app.py

This talks to the FastAPI backend over HTTP -- make sure it's running
first:
    uvicorn backend.main:app --reload

The dashboard itself has no business logic: it just calls the backend
endpoints and displays what comes back. Keeping it this thin means the
same backend could later serve a completely different frontend (React,
mobile, etc.) with no changes needed here.
"""

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="YouTube Toxic Comment Filter", layout="wide")
st.title("YouTube Toxic Comment Filter")

tab_vod, tab_live, tab_browse = st.tabs(
    ["Fetch VOD comments", "Fetch live chat", "Browse stored comments"]
)

with tab_vod:
    st.subheader("Fetch and classify comments from a regular video")
    video_id = st.text_input("Video ID (the part after v= in the URL)", key="vod_id")
    if st.button("Fetch VOD comments"):
        with st.spinner("Fetching and classifying..."):
            resp = requests.post(f"{BACKEND_URL}/fetch/vod/{video_id}")
        if resp.status_code == 200:
            data = resp.json()
            st.success(f"Fetched {data['fetched']} new comments")
            if data["results"]:
                st.dataframe(pd.DataFrame(data["results"]))
        else:
            st.error(resp.json().get("detail", "Something went wrong"))

with tab_live:
    st.subheader("Fetch and classify messages from an active live stream")
    live_video_id = st.text_input("Live video ID", key="live_id")
    if st.button("Fetch live chat batch"):
        with st.spinner("Fetching and classifying..."):
            resp = requests.post(f"{BACKEND_URL}/fetch/live/{live_video_id}")
        if resp.status_code == 200:
            data = resp.json()
            st.success(
                f"Fetched {data['fetched']} new messages "
                f"(next poll recommended in {data['poll_delay_seconds']:.1f}s)"
            )
            if data["results"]:
                st.dataframe(pd.DataFrame(data["results"]))
        else:
            try:
                detail = resp.json().get("detail", "Something went wrong")
            except Exception:
                detail = resp.text or "Something went wrong"

            st.error(detail)
            
with tab_browse:
    st.subheader("Stored comments")
    filter_video = st.text_input("Filter by video ID (optional)", key="browse_video")
    show_toxic_only = st.checkbox("Show only flagged-toxic comments")

    endpoint = "/comments/toxic" if show_toxic_only else "/comments"
    params = {"video_id": filter_video} if filter_video else {}
    resp = requests.get(f"{BACKEND_URL}{endpoint}", params=params)

    if resp.status_code == 200:
        comments = resp.json()
        if comments:
            df = pd.DataFrame(comments)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No comments stored yet -- fetch some from the other tabs first.")
    else:
        st.error("Could not reach the backend. Is uvicorn running?")
