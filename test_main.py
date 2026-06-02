import os
import pytest
import urllib.parse
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app, remove_file

client = TestClient(app)

def test_invalid_url():
    response = client.post("/download", json={"url": "https://example.com/not-a-video"})
    assert response.status_code == 400
    assert "Invalid YouTube URL" in response.json()["detail"]

def test_missing_url():
    response = client.post("/download", json={})
    assert response.status_code == 422 # FastAPI validation error

def test_is_valid_youtube_url_logic():
    from main import is_valid_youtube_url
    assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True
    assert is_valid_youtube_url("https://example.com") is False


def test_missing_cookies():
    # Ensure cookies.txt does not exist
    if os.path.exists("cookies.txt"):
        os.remove("cookies.txt")

    response = client.post("/download", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert response.status_code == 500
    assert "cookies.txt file not found" in response.json()["detail"]

@patch("main.yt_dlp.YoutubeDL")
def test_successful_download(mock_ydl):
    # Setup mock
    mock_ydl_instance = MagicMock()
    mock_ydl.return_value.__enter__.return_value = mock_ydl_instance

    # Create a dummy file to act as the downloaded file
    dummy_filepath = "test_dummy_video.mp4"
    with open(dummy_filepath, "w") as f:
        f.write("dummy content")

    mock_ydl_instance.extract_info.return_value = {
        "title": "Test Video | Title",
        "requested_downloads": [{"filepath": dummy_filepath}]
    }

    # Create a dummy cookies.txt file for test
    with open("cookies.txt", "w") as f:
        f.write("# Netscape HTTP Cookie File")

    response = client.post("/download", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})

    # Cleanup dummy file just in case background task didn't run in test context
    if os.path.exists(dummy_filepath):
        os.remove(dummy_filepath)
    if os.path.exists("cookies.txt"):
        os.remove("cookies.txt")

    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp4"
    expected_filename = urllib.parse.quote("Test Video  Title.mp4")
    assert expected_filename in response.headers["content-disposition"]
