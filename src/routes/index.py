from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from src.configs.configs import app_config

router = APIRouter()

from fastapi.responses import HTMLResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def root():
    html = """
    <html>
        <head>
            <title>FundOS</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                }
                .container {
                    text-align: center;
                    background-color: #fff;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                }
                h1 {
                    color: #2c3e50;
                    margin-bottom: 20px;
                }
                p {
                    color: #555;
                    font-size: 16px;
                    margin: 10px 0;
                }
                .footer {
                    margin-top: 30px;
                    font-size: 14px;
                    color: #888;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to FundOS</h1>
                <p>Version: 1.0.0</p>
                <p>We are under active development. Thank you for your patience.</p>
                <div class="footer">© 33 Art Ventures</div>
            </div>
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
