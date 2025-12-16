# Universal Video Downloader API

## Overview
A production-ready FastAPI backend API for downloading videos from multiple platforms (YouTube, TikTok, Instagram, Facebook, Twitter/X, Vimeo, Dailymotion, etc.) using yt-dlp.

## Project Structure
```
app/
├── __init__.py
├── main.py              # FastAPI application with endpoints
├── models.py            # Pydantic request/response models
├── services/
│   ├── __init__.py
│   ├── ytdlp_service.py # yt-dlp video extraction logic
│   └── logging_service.py # Request logging middleware
└── utils/
    └── __init__.py
requirements.txt         # Python dependencies
```

## API Endpoints

### GET /
API info and status

### GET /health
Simple health check returning `{"status": "healthy"}`

### POST /info
Get video metadata only (no download URL).

**Request Body:**
```json
{
  "url": "any supported video url"
}
```

**Success Response:**
```json
{
  "status": "success",
  "platform": "Youtube",
  "title": "video title",
  "description": "video description",
  "thumbnail": "thumbnail url",
  "duration": 123.45,
  "uploader": "channel name",
  "upload_date": "20241216",
  "view_count": 1000000,
  "like_count": 50000
}
```

### POST /qualities
List available quality options for a video.

**Request Body:**
```json
{
  "url": "any supported video url"
}
```

**Success Response:**
```json
{
  "status": "success",
  "platform": "Youtube",
  "title": "video title",
  "available_qualities": [
    {
      "format_id": "137",
      "quality": "1080p",
      "ext": "mp4",
      "filesize": 123456789,
      "has_audio": false,
      "has_video": true
    }
  ]
}
```

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
  "message": "human readable error message",
  "error_code": "ERROR_CODE"
}
```

## Error Codes
- `INVALID_URL` - URL format is invalid or not supported
- `VIDEO_UNAVAILABLE` - Video is private, deleted, or blocked
- `AUTH_REQUIRED` - Video requires authentication (age-restricted, private)
- `TIMEOUT` - Request timed out
- `EXTRACTION_ERROR` - General extraction failure
- `NO_DOWNLOAD_URL` - No downloadable URL found
- `VALIDATION_ERROR` - Request validation failed
- `AUTH_FAILED` - API key authentication failed

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
- IP-based rate limiting (10-20 requests/minute depending on endpoint)
- Request timeout protection (60 seconds)
- Retry logic with exponential backoff (3 attempts)
- CORS enabled for frontend consumption
- Request logging middleware
- Optional API key authentication
- Clean JSON responses with error codes

### Environment Variables
- `CORS_ORIGINS` - Comma-separated list of allowed origins (default: "*")
- `API_KEY` - Optional API key for protected endpoints

### Running Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## React Frontend Integration

### Basic Fetch Example
```javascript
const API_URL = 'https://your-api-url.replit.app';

async function getVideoInfo(url) {
  const response = await fetch(`${API_URL}/info`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // 'X-API-Key': 'your-api-key', // If API_KEY is set
    },
    body: JSON.stringify({ url }),
  });
  
  const data = await response.json();
  
  if (data.status === 'error') {
    throw new Error(data.message);
  }
  
  return data;
}

async function getDownloadLink(url, quality = 'best') {
  const response = await fetch(`${API_URL}/download`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url, quality }),
  });
  
  const data = await response.json();
  
  if (data.status === 'error') {
    throw new Error(data.message);
  }
  
  return data;
}

async function getAvailableQualities(url) {
  const response = await fetch(`${API_URL}/qualities`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
  });
  
  const data = await response.json();
  
  if (data.status === 'error') {
    throw new Error(data.message);
  }
  
  return data;
}
```

### React Hook Example
```javascript
import { useState, useCallback } from 'react';

function useVideoDownloader(apiUrl) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const fetchVideo = useCallback(async (url, quality = 'best') => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${apiUrl}/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, quality }),
      });
      
      const result = await response.json();
      
      if (result.status === 'error') {
        throw new Error(result.message);
      }
      
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  return { loading, error, data, fetchVideo };
}

export default useVideoDownloader;
```

## Supported Platforms
- YouTube
- TikTok
- Instagram
- Facebook
- Twitter/X
- Vimeo
- Dailymotion
- Reddit
- Twitch
- And 1000+ more via yt-dlp

## Recent Changes
- 2024-12-16: Added /info and /qualities endpoints
- 2024-12-16: Added request logging middleware
- 2024-12-16: Improved error handling with error codes
- 2024-12-16: Added retry logic with backoff
- 2024-12-16: Added optional API key authentication
- 2024-12-16: Added URL validation
- 2024-12-16: Initial project setup
