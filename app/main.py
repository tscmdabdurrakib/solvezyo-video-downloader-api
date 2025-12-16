import os
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio
from typing import Optional

from app.models import (
    DownloadRequest, InfoRequest, SuccessResponse, 
    InfoResponse, QualitiesResponse, ErrorResponse, QualityOption
)
from app.services.ytdlp_service import (
    extract_video_info, extract_metadata_only, extract_available_qualities,
    VideoExtractionError, URLValidationError, VideoUnavailableError, AuthenticationRequiredError
)
from app.services.logging_service import RequestLoggingMiddleware, log_rate_limit_hit

ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
API_KEY = os.environ.get("API_KEY", None)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Universal Video Downloader API",
    description="Production-ready API for downloading videos from multiple platforms using yt-dlp",
    version="2.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUEST_TIMEOUT = 60

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail={"status": "error", "message": "Invalid or missing API key", "error_code": "AUTH_FAILED"}
        )
    return True

def handle_extraction_error(e: Exception) -> JSONResponse:
    if isinstance(e, asyncio.TimeoutError):
        return JSONResponse(
            status_code=408,
            content=ErrorResponse(
                message="Request timed out. The video might be too large or the server is busy.",
                error_code="TIMEOUT"
            ).model_dump()
        )
    elif isinstance(e, URLValidationError):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(message=e.message, error_code=e.error_code).model_dump()
        )
    elif isinstance(e, VideoUnavailableError):
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(message=e.message, error_code=e.error_code).model_dump()
        )
    elif isinstance(e, AuthenticationRequiredError):
        return JSONResponse(
            status_code=403,
            content=ErrorResponse(message=e.message, error_code=e.error_code).model_dump()
        )
    elif isinstance(e, VideoExtractionError):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(message=e.message, error_code=e.error_code).model_dump()
        )
    elif isinstance(e, ValueError):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(message=str(e), error_code="VALIDATION_ERROR").model_dump()
        )
    else:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message=f"Internal server error: {str(e)}",
                error_code="INTERNAL_ERROR"
            ).model_dump()
        )

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Universal Video Downloader API",
        "version": "2.0.0",
        "endpoints": {
            "GET /health": "Health check",
            "POST /download": "Get video download link",
            "POST /info": "Get video metadata only",
            "POST /qualities": "List available quality options",
        },
        "documentation": "/docs",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/download", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def download_video(request: Request, body: DownloadRequest, _: bool = Depends(verify_api_key)):
    try:
        result = await asyncio.wait_for(
            extract_video_info(body.url, body.quality),
            timeout=REQUEST_TIMEOUT
        )
        
        return SuccessResponse(
            platform=result["platform"],
            title=result["title"],
            thumbnail=result.get("thumbnail"),
            duration=result.get("duration"),
            download_url=result["download_url"],
        )
        
    except Exception as e:
        return handle_extraction_error(e)

@app.post("/info", response_model=InfoResponse)
@limiter.limit("20/minute")
async def get_video_info(request: Request, body: InfoRequest, _: bool = Depends(verify_api_key)):
    try:
        result = await asyncio.wait_for(
            extract_metadata_only(body.url),
            timeout=REQUEST_TIMEOUT
        )
        
        return InfoResponse(
            platform=result["platform"],
            title=result["title"],
            description=result.get("description"),
            thumbnail=result.get("thumbnail"),
            duration=result.get("duration"),
            uploader=result.get("uploader"),
            upload_date=result.get("upload_date"),
            view_count=result.get("view_count"),
            like_count=result.get("like_count"),
        )
        
    except Exception as e:
        return handle_extraction_error(e)

@app.post("/qualities", response_model=QualitiesResponse)
@limiter.limit("20/minute")
async def get_available_qualities(request: Request, body: InfoRequest, _: bool = Depends(verify_api_key)):
    try:
        result = await asyncio.wait_for(
            extract_available_qualities(body.url),
            timeout=REQUEST_TIMEOUT
        )
        
        quality_options = [
            QualityOption(**q) for q in result["available_qualities"]
        ]
        
        return QualitiesResponse(
            platform=result["platform"],
            title=result["title"],
            available_qualities=quality_options,
        )
        
    except Exception as e:
        return handle_extraction_error(e)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
