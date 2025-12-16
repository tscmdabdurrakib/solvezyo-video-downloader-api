from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal

class DownloadRequest(BaseModel):
    url: str = Field(..., description="Video URL from any yt-dlp supported platform")
    quality: Literal["best", "worst", "360p", "720p", "1080p"] = Field(
        default="best",
        description="Video quality preference"
    )

class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    platform: str = Field(..., description="Detected platform name")
    title: str = Field(..., description="Video title")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    download_url: str = Field(..., description="Direct downloadable MP4 link")

class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str = Field(..., description="Human readable error message")
