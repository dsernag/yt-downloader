import os
import re
import uuid
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="yt-downloader", description="A lightweight API to download YouTube videos.")

class DownloadRequest(BaseModel):
    url: str

def is_valid_youtube_url(url: str) -> bool:
    """
    Validates if a given URL is a valid YouTube link.
    Matches standard youtube.com, youtu.be, and various formats.
    """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(re.match(youtube_regex, url))

def remove_file(path: str):
    """
    Background task to remove the file after it has been sent to the client.
    """
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            print(f"Error removing file {path}: {e}")

@app.post("/download")
def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    url = request.url

    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL provided. Please provide a valid youtube.com or youtu.be link.")

    # Generate a unique ID for the output file to avoid collisions on concurrent requests
    unique_id = str(uuid.uuid4())
    temp_filename_template = f"temp_{unique_id}.%(ext)s"

    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Best video + audio, merge to mp4
        'merge_output_format': 'mp4',
        'outtmpl': temp_filename_template,
        'noplaylist': True, # Only download a single video if a playlist is provided
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info to get the video title and actual file path
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'video')
            # ydl.prepare_filename returns the expected output filename
            # Note: Because of merge_output_format='mp4', yt-dlp might change the extension.
            # Using info_dict['ext'] directly might be the pre-merged extension,
            # so we explicitly replace the extension in the template with 'mp4' or just get the expected filename
            # However, extract_info with download=True populates 'requested_downloads' with the final file(s)

            if 'requested_downloads' in info_dict and info_dict['requested_downloads']:
                final_filepath = info_dict['requested_downloads'][0]['filepath']
            else:
                 # Fallback if requested_downloads is empty
                 final_filepath = ydl.prepare_filename(info_dict)
                 # Force .mp4 extension since we specified merge_output_format='mp4'
                 base, _ = os.path.splitext(final_filepath)
                 final_filepath = f"{base}.mp4"

            # Clean up the title to create a safe filename
            safe_title = re.sub(r'[\\/*?:"<>|]', "", video_title)
            download_filename = f"{safe_title}.mp4"

            # Check if file was actually created
            if not os.path.exists(final_filepath):
                raise HTTPException(status_code=500, detail="Video download failed. File not found.")

            # Schedule the temporary file for deletion after the response is sent
            background_tasks.add_task(remove_file, final_filepath)

            return FileResponse(
                path=final_filepath,
                filename=download_filename,
                media_type='video/mp4'
            )

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Failed to download video: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
