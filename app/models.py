from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List
import re

class DownloadRequest(BaseModel):
    url: str = Field(..., description="Video URL from any yt-dlp supported platform")
    quality: Literal["best", "worst", "360p", "720p", "1080p"] = Field(
        default="best",
        description="Video quality preference"
    )
    
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty")
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format")
        return v

class InfoRequest(BaseModel):
    url: str = Field(..., description="Video URL to get metadata")
    
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty")
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format")
        return v

class QualityOption(BaseModel):
    format_id: str = Field(..., description="Format identifier")
    quality: str = Field(..., description="Quality label (e.g., 720p, 1080p)")
    ext: str = Field(..., description="File extension")
    filesize: Optional[int] = Field(None, description="File size in bytes")
    has_audio: bool = Field(..., description="Whether format includes audio")
    has_video: bool = Field(..., description="Whether format includes video")

class SuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    platform: str = Field(..., description="Detected platform name")
    title: str = Field(..., description="Video title")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    download_url: str = Field(..., description="Direct downloadable MP4 link")

class InfoResponse(BaseModel):
    status: Literal["success"] = "success"
    platform: str = Field(..., description="Detected platform name")
    title: str = Field(..., description="Video title")
    description: Optional[str] = Field(None, description="Video description")
    thumbnail: Optional[str] = Field(None, description="Thumbnail URL")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    uploader: Optional[str] = Field(None, description="Video uploader/channel name")
    upload_date: Optional[str] = Field(None, description="Upload date (YYYYMMDD)")
    view_count: Optional[int] = Field(None, description="View count")
    like_count: Optional[int] = Field(None, description="Like count")

class QualitiesResponse(BaseModel):
    status: Literal["success"] = "success"
    platform: str = Field(..., description="Detected platform name")
    title: str = Field(..., description="Video title")
    available_qualities: List[QualityOption] = Field(..., description="List of available quality options")

class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    message: str = Field(..., description="Human readable error message")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
