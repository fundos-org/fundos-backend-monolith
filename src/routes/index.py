from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from src.configs.configs import app_config

router = APIRouter()

@router.get("/")
async def root():
    html = """
    <html>
        <head>
            <title>FastAPI</title>
        </head>
        <body>
            <h1>Welcome to FundOS (A part of 33 ART Ventures)</h1>
            <p>Version: 1.0.0</p>
            <p>We are under active development, thanks for your patience..</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html, media_type="text/html")

@router.get("/health")
async def health():
    return JSONResponse(
        status_code=200, 
        content={
            "message" : f"server is healthy and up and running on Port: {app_config.port}",
            "success": True, 
            "version": f"{app_config.version}"
            }
        )
