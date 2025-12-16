from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import asyncio

from app.models import DownloadRequest, SuccessResponse, ErrorResponse
from app.services.ytdlp_service import extract_video_info

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Universal Video Downloader API",
    description="Production-ready API for downloading videos from multiple platforms using yt-dlp",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUEST_TIMEOUT = 60

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Universal Video Downloader API",
        "version": "1.0.0",
        "endpoints": {
            "POST /download": "Download video from any supported platform"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/download", response_model=SuccessResponse)
@limiter.limit("10/minute")
async def download_video(request: Request, body: DownloadRequest):
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
        
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=408,
            content=ErrorResponse(
                message="Request timed out. The video might be too large or the server is busy."
            ).model_dump()
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(message=str(e)).model_dump()
        )
    except Exception as e:
        error_msg = str(e)
        
        if "Video unavailable" in error_msg:
            message = "Video is unavailable or private"
        elif "Unsupported URL" in error_msg:
            message = "This URL is not supported"
        elif "Sign in" in error_msg or "login" in error_msg.lower():
            message = "This video requires authentication"
        elif "age" in error_msg.lower():
            message = "This video is age-restricted"
        elif "copyright" in error_msg.lower() or "blocked" in error_msg.lower():
            message = "This video is blocked or unavailable in your region"
        else:
            message = f"Failed to process video: {error_msg}"
        
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(message=message).model_dump()
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
