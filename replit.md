# Universal Video Downloader API

## Overview
A production-ready FastAPI backend API for downloading videos from multiple platforms (YouTube, TikTok, Instagram, Facebook, Twitter/X, etc.) using yt-dlp.

## Project Structure
```
app/
├── __init__.py
├── main.py              # FastAPI application with endpoints
├── models.py            # Pydantic request/response models
├── services/
│   ├── __init__.py
│   └── ytdlp_service.py # yt-dlp video extraction logic
└── utils/
    └── __init__.py
requirements.txt         # Python dependencies
```

## API Endpoints

### GET /
Health check and API info

### GET /health
Simple health check returning `{"status": "healthy"}`

### POST /download
Download video information from any supported platform.

**Request Body:**
```json
{
  "url": "any supported video url",
  "quality": "best | worst | 360p | 720p | 1080p"
}
```

**Success Response:**
```json
{
  "status": "success",
  "platform": "detected platform name",
  "title": "video title",
  "thumbnail": "thumbnail url",
  "duration": 123.45,
  "download_url": "direct downloadable mp4 link"
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "human readable error message"
}
```

## Technical Details

### Dependencies
- FastAPI - Web framework
- yt-dlp - Video downloader engine
- ffmpeg - Audio/video merging (system package)
- uvicorn - ASGI server
- slowapi - Rate limiting

### Features
- Universal platform support via yt-dlp auto-detection
- MP4 format with audio/video merging
- IP-based rate limiting (10 requests/minute)
- Request timeout protection (60 seconds)
- CORS enabled for frontend consumption
- Clean JSON responses

### Running Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## Recent Changes
- 2024-12-16: Initial project setup with complete API implementation
