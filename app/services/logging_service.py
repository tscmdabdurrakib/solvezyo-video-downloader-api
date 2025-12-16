import logging
import time
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""
        
        request_body = None
        if method == "POST" and path in ["/download", "/info", "/qualities"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    request_body = json.loads(body_bytes.decode())
                    if "url" in request_body:
                        request_body["url"] = mask_url(request_body["url"])
            except:
                pass
        
        response = await call_next(request)
        
        latency = time.time() - start_time
        latency_ms = round(latency * 1000, 2)
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
            "method": method,
            "path": path,
            "query": query,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
        }
        
        if request_body:
            log_data["request_body"] = request_body
        
        if response.status_code >= 400:
            logger.warning(f"Request failed: {json.dumps(log_data)}")
        else:
            logger.info(f"Request completed: {json.dumps(log_data)}")
        
        return response

def mask_url(url: str) -> str:
    if len(url) > 50:
        return url[:30] + "..." + url[-15:]
    return url

def log_rate_limit_hit(client_ip: str, endpoint: str):
    logger.warning(f"Rate limit hit: ip={client_ip}, endpoint={endpoint}")
