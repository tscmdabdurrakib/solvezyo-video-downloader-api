import yt_dlp
from typing import Dict, Any, List
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import logging

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=4)

QUALITY_MAP = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "worst": "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
    "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best",
}

MAX_RETRIES = 3
RETRY_DELAY = 1.0

class VideoExtractionError(Exception):
    def __init__(self, message: str, error_code: str = "EXTRACTION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class URLValidationError(VideoExtractionError):
    def __init__(self, message: str):
        super().__init__(message, "INVALID_URL")

class VideoUnavailableError(VideoExtractionError):
    def __init__(self, message: str):
        super().__init__(message, "VIDEO_UNAVAILABLE")

class AuthenticationRequiredError(VideoExtractionError):
    def __init__(self, message: str):
        super().__init__(message, "AUTH_REQUIRED")

def get_ydl_opts(quality: str = "best", for_info_only: bool = False) -> Dict[str, Any]:
    format_str = QUALITY_MAP.get(quality, QUALITY_MAP["best"])
    
    opts = {
        "format": format_str,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "noplaylist": True,
        "geo_bypass": True,
        "socket_timeout": 30,
    }
    
    if for_info_only:
        opts["skip_download"] = True
    
    return opts

def _extract_with_retry(url: str, opts: Dict[str, Any], max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    last_error = None
    
    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info is None:
                    raise VideoExtractionError("Could not extract video information")
                
                return info
                
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            last_error = e
            
            if "Video unavailable" in error_msg or "Private video" in error_msg:
                raise VideoUnavailableError("Video is unavailable or private")
            elif "Unsupported URL" in error_msg:
                raise URLValidationError("This URL is not supported by any available extractor")
            elif "Sign in" in error_msg or "login" in error_msg.lower():
                raise AuthenticationRequiredError("This video requires authentication to access")
            elif "age" in error_msg.lower():
                raise AuthenticationRequiredError("This video is age-restricted and requires authentication")
            elif "copyright" in error_msg.lower() or "blocked" in error_msg.lower():
                raise VideoUnavailableError("This video is blocked or unavailable in your region")
            
            if attempt < max_retries - 1:
                backoff_delay = RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {backoff_delay}s: {error_msg}")
                time.sleep(backoff_delay)
            else:
                raise VideoExtractionError(f"Failed after {max_retries} attempts: {error_msg}")
                
        except yt_dlp.utils.ExtractorError as e:
            error_msg = str(e)
            raise VideoExtractionError(f"Extractor error: {error_msg}")
            
        except Exception as e:
            if attempt < max_retries - 1:
                backoff_delay = RETRY_DELAY * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed with unexpected error, retrying in {backoff_delay}s: {str(e)}")
                time.sleep(backoff_delay)
            else:
                raise VideoExtractionError(f"Unexpected error: {str(e)}")
    
    raise VideoExtractionError(f"Failed after {max_retries} attempts")

def _normalize_platform(extractor: str) -> str:
    platform = extractor
    if platform.endswith(":tab"):
        platform = platform[:-4]
    return platform.replace("_", " ").title()

async def extract_video_info(url: str, quality: str = "best") -> Dict[str, Any]:
    loop = asyncio.get_event_loop()
    opts = get_ydl_opts(quality)
    info = await loop.run_in_executor(executor, _extract_with_retry, url, opts, MAX_RETRIES)
    
    platform = _normalize_platform(info.get("extractor", "unknown"))
    title = info.get("title", "Unknown Title")
    thumbnail = info.get("thumbnail")
    duration = info.get("duration")
    download_url = get_best_download_url(info)
    
    return {
        "platform": platform,
        "title": title,
        "thumbnail": thumbnail,
        "duration": duration,
        "download_url": download_url,
    }

async def extract_metadata_only(url: str) -> Dict[str, Any]:
    loop = asyncio.get_event_loop()
    opts = get_ydl_opts("best", for_info_only=True)
    info = await loop.run_in_executor(executor, _extract_with_retry, url, opts, MAX_RETRIES)
    
    platform = _normalize_platform(info.get("extractor", "unknown"))
    
    return {
        "platform": platform,
        "title": info.get("title", "Unknown Title"),
        "description": info.get("description"),
        "thumbnail": info.get("thumbnail"),
        "duration": info.get("duration"),
        "uploader": info.get("uploader") or info.get("channel"),
        "upload_date": info.get("upload_date"),
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
    }

async def extract_available_qualities(url: str) -> Dict[str, Any]:
    loop = asyncio.get_event_loop()
    opts = get_ydl_opts("best", for_info_only=True)
    info = await loop.run_in_executor(executor, _extract_with_retry, url, opts, MAX_RETRIES)
    
    platform = _normalize_platform(info.get("extractor", "unknown"))
    formats = info.get("formats", [])
    
    quality_options = []
    seen_qualities = set()
    
    for fmt in formats:
        if not fmt.get("url"):
            continue
            
        height = fmt.get("height")
        ext = fmt.get("ext", "unknown")
        format_id = fmt.get("format_id", "")
        
        has_video = fmt.get("vcodec") != "none" and fmt.get("vcodec") is not None
        has_audio = fmt.get("acodec") != "none" and fmt.get("acodec") is not None
        
        if height:
            quality_label = f"{height}p"
        elif has_audio and not has_video:
            quality_label = "audio only"
        else:
            quality_label = fmt.get("format_note", "unknown")
        
        quality_key = f"{quality_label}_{ext}_{has_audio}"
        if quality_key in seen_qualities:
            continue
        seen_qualities.add(quality_key)
        
        quality_options.append({
            "format_id": format_id,
            "quality": quality_label,
            "ext": ext,
            "filesize": fmt.get("filesize") or fmt.get("filesize_approx"),
            "has_audio": has_audio,
            "has_video": has_video,
        })
    
    quality_options.sort(key=lambda x: (
        0 if x["has_video"] else 1,
        -int(x["quality"].replace("p", "")) if x["quality"].endswith("p") else 0
    ))
    
    return {
        "platform": platform,
        "title": info.get("title", "Unknown Title"),
        "available_qualities": quality_options,
    }

def get_best_download_url(info: Dict[str, Any]) -> str:
    if "url" in info and info["url"]:
        return info["url"]
    
    formats = info.get("formats", [])
    
    mp4_formats = [f for f in formats if f.get("ext") == "mp4" and f.get("url")]
    
    if mp4_formats:
        video_audio = [f for f in mp4_formats if f.get("vcodec") != "none" and f.get("acodec") != "none"]
        if video_audio:
            best = max(video_audio, key=lambda x: (x.get("height") or 0, x.get("tbr") or 0))
            return best["url"]
        
        video_only = [f for f in mp4_formats if f.get("vcodec") != "none"]
        if video_only:
            best = max(video_only, key=lambda x: (x.get("height") or 0, x.get("tbr") or 0))
            return best["url"]
    
    if formats:
        for fmt in reversed(formats):
            if fmt.get("url"):
                return fmt["url"]
    
    if info.get("requested_formats"):
        for fmt in info["requested_formats"]:
            if fmt.get("url"):
                return fmt["url"]
    
    raise VideoExtractionError("No downloadable URL found for this video", "NO_DOWNLOAD_URL")
