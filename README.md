# yt-downloader

A lightweight FastAPI application in Python to download YouTube videos in the best possible quality as `.mp4` files using `yt-dlp`.

## Requirements

To run this application, you need Python 3.8+ and `ffmpeg` installed on your system. `ffmpeg` is strictly required by `yt-dlp` to merge the best quality video and audio streams into a single `.mp4` file.

### Installing FFmpeg

**Windows:**
1. Download a Windows build from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or [BtbN](https://github.com/BtbN/FFmpeg-Builds/releases).
2. Extract the archive and add the `bin` folder to your system's `PATH` environment variable.
3. Alternatively, if you use a package manager like `winget` or `choco`:
   - `winget install ffmpeg`
   - `choco install ffmpeg`

**macOS:**
You can install `ffmpeg` using Homebrew:
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Installing Python Dependencies

1. Clone this repository.
2. It's recommended to create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the FastAPI server using `uvicorn`:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. You can also view the interactive API documentation at `http://localhost:8000/docs`.

## Usage

### Endpoint: `POST /download`

Downloads a YouTube video and returns it as a file attachment, allowing your browser or client to prompt you for a download destination, defaulting to the video's title (`<video_name>.mp4`).

**Request Body (JSON):**
```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Responses:**
- `200 OK`: Returns the `.mp4` video file as an attachment.
- `400 Bad Request`: If the provided URL is not a valid YouTube link.
- `500 Internal Server Error`: If an error occurs during the download process.

**Example using `curl`:**
```bash
curl -X POST "http://localhost:8000/download" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' \
     --output downloaded_video.mp4
```
