from os import getenv
from typing import List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, conint

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

class HeaderStr(str):
    """__HeaderStr class__
        This is to allow a contains comparison for the match statments
    Args:
        str (_type_): a regular sting

    example:
        print(HeaderStr(''text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7') == 'text/html')
        True
    """
    __eq__ = str.__contains__

# Models for post

class WledColourModel(BaseModel):
    root: List[conint(ge=0, le=255)] = Field(..., min_items=3, max_items=3) # type: ignore # RGB values

class WledPostModel(BaseModel):
    on: bool
    bri: conint(ge=0, le=255)  # type: ignore # Brightness
    colour: List[WledColourModel]  # Primary and secondary colors
    text: str  # Text for the scrolling effect
    speed: conint(ge=0, le=255)  # type: ignore # Speed

    def to_wled_payload(self):
        return {
            "on": self.on,
            "bri": self.bri,
            "seg": [
                {
                    "id": 0,  # Default main segment ID
                    "start": 0,  # Start of segment
                    "stop": 256,  # Adjust for your matrix size
                    "fx": 122,  # Effect ID for scrolling text
                    "sx": self.speed,  # Speed
                    "ix": 128,  # Default intensity
                    "col": [color.root for color in self.colour],  # Colors
                    "n": self.text,  # Scrolling text
                    "on": True,  # Keep segment on
                    "frz": False  # Segment not frozen
                }
            ]
        }
# Temp config


WLED_IP = getenv("WLED_IP","192.168.4.148")
PAGE_TITLE = getenv("PAGE_TITLE", "WLED Matrix test")
BS_THEME = getenv("BS_THEME", "dark")
API_URL = getenv("API_URL", "127.0.0.1:8000")
# Routes


@app.get("/")
async def read_root(request: Request):
    accept = HeaderStr(request.headers.get('accept', ''))
    match accept:
        case 'text/html':
            return templates.TemplateResponse("index.html", {"request": request, "page_title": PAGE_TITLE, "bs_theme": BS_THEME, "api_url": API_URL})
        case _:
            return {"message": "Try requesting the page with a browser"}
        
@app.get("/admin")
async def admin_root(request: Request):
    accept = HeaderStr(request.headers.get('accept', ''))
    match accept:
        case 'text/html':
            return templates.TemplateResponse("admin.html", {"request": request, "page_title": PAGE_TITLE, "bs_theme": BS_THEME, "api_url": API_URL})
        case _:
            return {"message": "Try requesting the page with a browser"}


@app.get("/wled/status")
@app.get("/wled/status/", include_in_schema=False)
async def read_status(request: Request):
    """
    Get WLED status
    """
    accept = HeaderStr(request.headers.get('accept', ''))
    match accept:
        case 'application/json':
            url = f"http://{WLED_IP}/json"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                wled_data = response.json()
                response.raise_for_status()
            return wled_data
        case _:
            return "Try application/json"


@app.post("/wled/matrix/text")
@app.post("/wled/matrix/text/", include_in_schema=False)
async def post_matrix_text(request: Request, data: WledPostModel):
    """
    Post text to WLED matrix
    """
    with open('logs/wledapi.log', 'a') as f:
        f.write(f"{data}\n")

    url = f"http://{WLED_IP}/json"
    # print(data.to_wled_payload())
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data.to_wled_payload())
        response.raise_for_status()
    return response.json()
