from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from services.tts_service import TTSService
from typing import Optional

router = APIRouter()
tts_service = TTSService()

class TTSRequest(BaseModel):
    text: str
    language: str
    cache_key: Optional[str] = None

@router.post("/api/tts")
async def create_speech(request: Request, tts_request: TTSRequest):
    try:
        audio_path = await tts_service.text_to_speech(tts_request.text, tts_request.language)
        base_url = str(request.base_url).rstrip('/')
        audio_url = f"{base_url}{audio_path}"
        return {
            "success": True,
            "audio_url": audio_url,
            "text": tts_request.text,
            "language": tts_request.language
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/tts/voices")
def get_voices():
    return {
        "success": True,
        "voices": tts_service.get_available_voices()
    } 