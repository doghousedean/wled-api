from typing import List
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, conint, Field
import httpx

app = FastAPI()
templates = Jinja2Templates(directory="templates")


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


WLED_IP = "192.168.4.148"

# Routes


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/wled/status")
@app.get("/wled/status/", include_in_schema=False)
async def read_status(request: Request):
    """
    Get WLED status
    """
    url = f"http://{WLED_IP}/json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        wled_data = response.json()
        response.raise_for_status()
    return wled_data


@app.post("/wled/matrix/text")
@app.post("/wled/matrix/text/", include_in_schema=False)
async def post_matrix_text(request: Request, data: WledPostModel):
    """
    Post text to WLED matrix
    """


    url = f"http://{WLED_IP}/json"
    # print(data.to_wled_payload())
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data.to_wled_payload())
        response.raise_for_status()
    return response.json()
