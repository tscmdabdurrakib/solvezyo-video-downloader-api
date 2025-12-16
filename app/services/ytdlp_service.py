import yt_dlp
from typing import Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

QUALITY_MAP = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "worst": "worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
    "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best",
}

def get_ydl_opts(quality: str = "best") -> Dict[str, Any]:
    format_str = QUALITY_MAP.get(quality, QUALITY_MAP["best"])
    
    return {
        "format": format_str,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "noplaylist": True,
        "geo_bypass": True,
        "socket_timeout": 30,
    }

def _extract_info(url: str, quality: str) -> Dict[str, Any]:
    opts = get_ydl_opts(quality)
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        if info is None:
            raise ValueError("Could not extract video information")
        
        return info

async def extract_video_info(url: str, quality: str = "best") -> Dict[str, Any]:
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(executor, _extract_info, url, quality)
    
    platform = info.get("extractor", "unknown")
    if platform.endswith(":tab"):
        platform = platform[:-4]
    platform = platform.replace("_", " ").title()
    
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
    
    raise ValueError("No downloadable URL found for this video")
