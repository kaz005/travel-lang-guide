from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Optional
from models import TouristSpot
import os
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder

load_dotenv()

app = FastAPI(title="Travel Language Guide API")

# テンプレートとスタティックファイルの設定
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, lang: str = 'ja'):
    spots = TouristSpot.load_spots()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "spots": spots,
            "current_lang": lang
        }
    )

@app.get("/spots/{spot_id}", response_class=HTMLResponse)
async def spot_detail(request: Request, spot_id: int, lang: str = 'ja'):
    spots = TouristSpot.load_spots()
    spot = next((spot for spot in spots if spot.id == spot_id), None)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "spot": spot,
            "current_lang": lang
        }
    )

@app.get("/map", response_class=HTMLResponse)
async def map_view(request: Request, lang: str = 'ja'):
    spots = TouristSpot.load_spots()
    return templates.TemplateResponse(
        "map.html",
        {
            "request": request,
            "spots": jsonable_encoder([spot.to_dict() for spot in spots]),
            "current_lang": lang
        }
    )

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    spots = TouristSpot.load_spots()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "spots": jsonable_encoder([spot.to_dict() for spot in spots])
        }
    )

@app.post("/admin/spots/create")
async def create_spot(
    request: Request,
    name_ja: str = Form(...),
    name_en: str = Form(...),
    name_zh: str = Form(...),
    desc_ja: str = Form(...),
    desc_en: str = Form(...),
    desc_zh: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    image_urls: List[str] = Form([]),
    image_captions_ja: List[str] = Form([]),
    image_captions_en: List[str] = Form([]),
    image_captions_zh: List[str] = Form([]),
):
    data = {
        "name": {
            "ja": name_ja,
            "en": name_en,
            "zh": name_zh
        },
        "description": {
            "ja": desc_ja,
            "en": desc_en,
            "zh": desc_zh
        },
        "coordinates": {
            "lat": lat,
            "lng": lng
        },
        "images": [
            {
                "url": url,
                "caption": {
                    "ja": cap_ja,
                    "en": cap_en,
                    "zh": cap_zh
                }
            }
            for url, cap_ja, cap_en, cap_zh in zip(
                image_urls, image_captions_ja, image_captions_en, image_captions_zh
            )
            if url.strip()  # 空のURLは除外
        ]
    }
    TouristSpot.create(data)
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@app.post("/admin/spots/{spot_id}/update")
async def update_spot(
    spot_id: int,
    name_ja: str = Form(...),
    name_en: str = Form(...),
    name_zh: str = Form(...),
    desc_ja: str = Form(...),
    desc_en: str = Form(...),
    desc_zh: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
    image_urls: Optional[List[str]] = Form(None),
    image_captions_ja: Optional[List[str]] = Form(None),
    image_captions_en: Optional[List[str]] = Form(None),
    image_captions_zh: Optional[List[str]] = Form(None),
):
    # 既存のスポットデータを取得
    spots = TouristSpot.load_spots()
    existing_spot = next((spot for spot in spots if spot.id == spot_id), None)
    if not existing_spot:
        raise HTTPException(status_code=404, detail="Spot not found")

    # 基本データの更新
    data = {
        "name": {
            "ja": name_ja,
            "en": name_en,
            "zh": name_zh
        },
        "description": {
            "ja": desc_ja,
            "en": desc_en,
            "zh": desc_zh
        },
        "coordinates": {
            "lat": lat,
            "lng": lng
        }
    }

    # 画像データの処理
    if image_urls is not None:
        data["images"] = [
            {
                "url": url,
                "caption": {
                    "ja": cap_ja,
                    "en": cap_en,
                    "zh": cap_zh
                }
            }
            for url, cap_ja, cap_en, cap_zh in zip(
                image_urls, image_captions_ja, image_captions_en, image_captions_zh
            )
            if url.strip()  # 空のURLは除外
        ]
    else:
        # 画像データが送信されていない場合は既存の画像を維持
        data["images"] = existing_spot.images

    try:
        TouristSpot.update(spot_id, data)
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    except ValueError:
        raise HTTPException(status_code=404, detail="Spot not found")

@app.post("/admin/spots/{spot_id}/delete")
async def delete_spot(spot_id: int):
    if TouristSpot.delete(spot_id):
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    raise HTTPException(status_code=404, detail="Spot not found") 