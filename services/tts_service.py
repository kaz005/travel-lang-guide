import os
import openai
from pathlib import Path
import hashlib
import json
from dotenv import load_dotenv

class TTSService:
    def __init__(self):
        # 環境変数を確実に読み込む
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        openai.api_key = api_key
        self.cache_dir = Path('static/audio_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.voices = {
            'ja': 'nova',      # 日本語に最適な音声
            'en': 'fable',     # 英語に最適な音声（より自然な英語発音）
            'zh': 'alloy'      # 中国語に最適な音声
        }

    def _get_cache_path(self, text: str, lang: str) -> Path:
        """キャッシュファイルのパスを生成"""
        # テキストと言語からハッシュを生成
        text_hash = hashlib.md5(f"{text}_{lang}".encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.mp3"

    def _save_metadata(self, text: str, lang: str, file_path: str):
        """音声ファイルのメタデータを保存"""
        metadata_path = Path(file_path).with_suffix('.json')
        metadata = {
            'text': text,
            'language': lang,
            'voice': self.voices[lang],
            'created_at': str(Path(file_path).stat().st_mtime)
        }
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    async def text_to_speech(self, text: str, lang: str) -> str:
        """テキス���を音声に変換し、ファイルパスを返す"""
        if not text or lang not in self.voices:
            print(f"[ERROR] Invalid input - Text: {text}, Language: {lang}")
            print(f"[ERROR] Available languages: {list(self.voices.keys())}")
            raise ValueError("Invalid text or language")

        print(f"[DEBUG] TTS Request - Text: {text}")
        print(f"[DEBUG] TTS Language: {lang}")
        print(f"[DEBUG] Selected voice: {self.voices[lang]}")

        cache_path = self._get_cache_path(text, lang)
        
        # キャッシュが存在する場合はそれを返す
        if cache_path.exists():
            print(f"[DEBUG] Using cached audio: {cache_path}")
            return f"/static/audio_cache/{cache_path.name}"

        print(f"[DEBUG] Generating new speech - Language: {lang}, Voice: {self.voices[lang]}")
        try:
            # 言語に応じて速度を調整
            speed = 1.0
            if lang == 'zh':
                speed = 0.9  # 中国語はやや遅めに
            elif lang == 'en':
                speed = 1.0  # 英語は標準速度（fableは自然な速度が良い）

            print(f"[DEBUG] TTS parameters - Speed: {speed}")

            # OpenAI APIを使用して音声を生成
            response = openai.audio.speech.create(
                model="tts-1",
                voice=self.voices[lang],
                input=text,
                speed=speed,
                response_format="mp3"
            )

            # 音声ファイルを保存
            with open(str(cache_path), 'wb') as f:
                f.write(response.content)
            print(f"[DEBUG] Audio file saved: {cache_path}")
            
            # 音声ファイルのURLパスを返す
            return f"/static/audio_cache/{cache_path.name}"

        except Exception as e:
            print(f"[ERROR] TTS generation failed: {str(e)}")
            print(f"[ERROR] Error type: {type(e)}")
            import traceback
            print(traceback.format_exc())
            if cache_path.exists():
                cache_path.unlink()
            raise

    def get_available_voices(self) -> dict:
        """利用可能な音声の一覧を返す"""
        return self.voices.copy()

    def clean_cache(self, max_age_days: int = 7):
        """古いキャッシュファイルを削除"""
        import time
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        for file in self.cache_dir.glob('*.mp3'):
            if current_time - file.stat().st_mtime > max_age_seconds:
                file.unlink()
                # メタデータファイルも削除
                metadata_file = file.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink() 