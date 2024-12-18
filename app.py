from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Optional
from models import TouristSpot
from routers import tts_router
import os
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from services.interpreter import interpreter_service
import uuid
from fastapi import WebSocket, WebSocketDisconnect
import json
import shutil
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Travel Language Guide API")

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory="static"), name="static")

# テンプレートの設定
templates = Jinja2Templates(directory="templates")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TTSルーターを追加
app.include_router(tts_router.router)

# WebSocketエンドポイントを追加
@app.websocket("/ws/interpreter")
async def websocket_interpreter(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    try:
        await interpreter_service.connect(websocket, client_id)
        print(f"Client connected: {client_id}")  # デバッグ用
        
        while True:
            try:
                data = await websocket.receive_json()
                print(f"Received data type: {data.get('type')}")  # デバッグ用
                
                if data["type"] == "audio":
                    await interpreter_service.process_audio(
                        data["data"],
                        data["lang"],
                        client_id
                    )
            except WebSocketDisconnect:
                print(f"Client disconnected: {client_id}")  # デバッグ用
                interpreter_service.disconnect(client_id)
                break
            except Exception as e:
                print(f"Error processing message: {str(e)}")  # デバッグ用
                break
    except Exception as e:
        print(f"Connection error: {str(e)}")  # デバッグ用
    finally:
        interpreter_service.disconnect(client_id)

# 翻訳用の辞書
translations = {
    'ja': {
        '観光スポット一覧': '観光スポット一覧',
        '各スポットの詳細情報を見るには画像をクリックしてください。': '各スポットの詳細情報を見るには画像をクリックしてください。',
        '管理ダッシュボード': '管理ダッシュボード',
        '詳細を見る': '詳細を見る',
        '音声を再生': '音声を再生'
    },
    'en': {
        '観光スポット一覧': 'Tourist Spots',
        '各スポットの詳細情報を見るには画像をクリックしてください。': 'Click on the image to see details of each spot.',
        '管理ダッシュボード': 'Admin Dashboard',
        '詳細を見る': 'View Details',
        '音声を再生': 'Play Audio'
    },
    'zh': {
        '観光スポット一覧': '观光景点一览',
        '各スポットの詳細情報を見るには画像をクリックしてください。': '点击图片查看每个景点的详细信息。',
        '管理ダッシュボード': '管理仪表板',
        '詳細を見る': '查看详情',
        '音声を再生': '播放音频'
    }
}

def get_translation(text: str, lang: str) -> str:
    """指定された言語でテキストを翻訳する"""
    return translations.get(lang, {}).get(text, text)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, lang: str = 'ja'):
    spots = TouristSpot.load_spots()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "spots": spots,
            "lang": lang,
            "_": lambda text: get_translation(text, lang)
        }
    )

@app.get("/spots/{spot_id}", response_class=HTMLResponse)
async def spot_detail(request: Request, spot_id: int, lang: str = 'ja'):
    spots = TouristSpot.load_spots()
    spot = next((spot for spot in spots if spot['id'] == spot_id), None)
    if not spot:
        raise HTTPException(status_code=404, detail="Spot not found")
    
    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "spot": spot,
            "current_lang": lang,
            "lang": lang
        }
    )

@app.get("/map", response_class=HTMLResponse)
async def map_view(request: Request, lang: str = 'ja'):
    spots = TouristSpot.load_spots()
    print(f"[DEBUG] Loaded spots for map: {spots}")  # デバッグ用
    return templates.TemplateResponse(
        "map.html",
        {
            "request": request,
            "spots": spots,
            "current_lang": lang,
            "lang": lang,
            "_": lambda text: get_translation(text, lang)
        }
    )

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, lang: str = 'ja'):
    spots = TouristSpot.load_spots()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "spots": jsonable_encoder(spots),
            "current_lang": lang,
            "lang": lang,
            "_": lambda text: get_translation(text, lang)
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
):
    # フォームデータを直接取得
    form = await request.form()
    
    # 画像関連のデータを配列として取得
    image_urls = form.getlist('image_urls[]')
    image_types = form.getlist('image_types[]')
    image_captions_ja = form.getlist('image_captions_ja[]')
    image_captions_en = form.getlist('image_captions_en[]')
    image_captions_zh = form.getlist('image_captions_zh[]')
    image_descriptions_ja = form.getlist('image_descriptions_ja[]')
    image_descriptions_en = form.getlist('image_descriptions_en[]')
    image_descriptions_zh = form.getlist('image_descriptions_zh[]')

    print(f"[DEBUG] Received image data: URLs={image_urls}, Types={image_types}")

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
                "type": img_type,
                "caption": {
                    "ja": cap_ja,
                    "en": cap_en,
                    "zh": cap_zh
                },
                "description": {
                    "ja": desc_ja,
                    "en": desc_en,
                    "zh": desc_zh
                }
            }
            for url, img_type, cap_ja, cap_en, cap_zh, desc_ja, desc_en, desc_zh in zip(
                image_urls,
                image_types,
                image_captions_ja,
                image_captions_en,
                image_captions_zh,
                image_descriptions_ja,
                image_descriptions_en,
                image_descriptions_zh
            )
            if url and url.strip()
        ]
    }

    print(f"[DEBUG] Processed data: {data}")
    TouristSpot.create(data)
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@app.post("/admin/spots/{spot_id}/update")
async def update_spot(
    request: Request,
    spot_id: int,
    name_ja: str = Form(...),
    name_en: str = Form(...),
    name_zh: str = Form(...),
    desc_ja: str = Form(...),
    desc_en: str = Form(...),
    desc_zh: str = Form(...),
    lat: float = Form(...),
    lng: float = Form(...),
):
    # フォームデータを直接取得
    form = await request.form()
    
    # 画像関連のデータを配列として取得
    image_urls = form.getlist('image_urls[]')
    image_types = form.getlist('image_types[]')
    image_captions_ja = form.getlist('image_captions_ja[]')
    image_captions_en = form.getlist('image_captions_en[]')
    image_captions_zh = form.getlist('image_captions_zh[]')
    image_descriptions_ja = form.getlist('image_descriptions_ja[]')
    image_descriptions_en = form.getlist('image_descriptions_en[]')
    image_descriptions_zh = form.getlist('image_descriptions_zh[]')

    print(f"[DEBUG] Received image data: URLs={image_urls}, Types={image_types}")

    data = {
        "id": spot_id,
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
                "type": img_type,
                "caption": {
                    "ja": cap_ja,
                    "en": cap_en,
                    "zh": cap_zh
                },
                "description": {
                    "ja": desc_ja,
                    "en": desc_en,
                    "zh": desc_zh
                }
            }
            for url, img_type, cap_ja, cap_en, cap_zh, desc_ja, desc_en, desc_zh in zip(
                image_urls,
                image_types,
                image_captions_ja,
                image_captions_en,
                image_captions_zh,
                image_descriptions_ja,
                image_descriptions_en,
                image_descriptions_zh
            )
            if url and url.strip()
        ]
    }

    print(f"[DEBUG] Processed update data: {data}")
    TouristSpot.update(spot_id, data)
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@app.post("/admin/spots/{spot_id}/delete")
async def delete_spot(spot_id: int):
    if TouristSpot.delete(spot_id):
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    raise HTTPException(status_code=404, detail="Spot not found") 