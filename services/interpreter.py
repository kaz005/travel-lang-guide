from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
import io
import soundfile as sf
import asyncio
from typing import Dict, Optional
import httpx
import base64
import json
import tempfile
import os
from openai import OpenAI
from services.tts_service import TTSService
import starlette.websockets
from dotenv import load_dotenv

class InterpreterService:
    def __init__(self):
        # OpenAI APIの設定
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI()
        self.active_connections = {}
        self.translation_modes = {}  # クライアントごとの言語モード（'ja', 'en', 'zh'）
        self.tts_service = TTSService()

    async def connect(self, websocket: WebSocket, client_id: str):
        """WebSocket接続の初期処理"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected")

        try:
            while True:
                message = await websocket.receive_json()
                await self.handle_message(message, client_id)
        except WebSocketDisconnect:
            print(f"Client {client_id} disconnected")
        except Exception as e:
            print(f"Connection error: {str(e)}")
        finally:
            self.disconnect(client_id)

    def disconnect(self, client_id: str):
        """クライアントの切断処理"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.translation_modes:
            del self.translation_modes[client_id]
        print(f"Client {client_id} cleanup completed")

    async def handle_message(self, message: dict, client_id: str):
        """WebSocketメッセージの処理"""
        try:
            message_type = message.get('type')
            print(f"Received message type: {message_type}")
            print(f"Full message: {message}")

            if message_type == 'mode':
                mode = message.get('mode', 'en')
                self.translation_modes[client_id] = mode
                print(f"Set language mode for client {client_id} to: {mode}")
            
            elif message_type == 'audio':
                mode = message.get('mode')
                if not mode:
                    mode = self.translation_modes.get(client_id, 'en')
                print(f"Processing audio with mode: {mode}")
                await self.process_audio(
                    message.get('data', ''),
                    message.get('source_lang', 'en'),
                    client_id,
                    mode
                )
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(traceback.format_exc())

    async def process_audio(self, audio_data: str, source_lang: str, client_id: str, mode: str):
        """音声データを処理し、翻訳と音声合成を行う"""
        try:
            print(f"Starting audio processing in {mode} mode")
            # Base64デコード
            try:
                if ',' in audio_data:
                    audio_bytes = base64.b64decode(audio_data.split(',')[1])
                else:
                    audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                print(f"Base64 decoding error: {str(e)}")
                return

            print(f"Successfully decoded audio data, size: {len(audio_bytes)} bytes")
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            # 言語コードの変換マップ
            LANG_CODE_MAP = {
                'japanese': 'ja',
                'english': 'en',
                'chinese': 'zh',
                'ja': 'ja',
                'en': 'en',
                'zh': 'zh'
            }

            # OpenAI Whisper APIを使用した音声認識
            with open(temp_path, 'rb') as audio_file:
                # まず言語検出を行う
                detect_result = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="verbose_json"
                )
                detected_lang = detect_result.language.lower()
                iso_lang = LANG_CODE_MAP.get(detected_lang, 'en')  # デフォルトは英語

                # ファイルポインタを先頭に戻す
                audio_file.seek(0)
                
                # 検出された言語で再度音声認識を実行
                result = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    language=iso_lang
                )
            
            text = result.text.strip()
            
            # 一時ファイルを削除
            os.unlink(temp_path)
            
            print(f"Recognized text: {text}")
            print(f"Detected language: {iso_lang}")
            print(f"Processing in mode: {mode}")
            
            if text:
                # 翻訳を実行
                await self._send_translation(text, iso_lang, client_id, mode)
            else:
                print("No text recognized from audio")

        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(traceback.format_exc())

    async def _translate_text(self, text: str, detected_lang: str, mode: str) -> Optional[str]:
        """テキストを翻訳"""
        try:
            print(f"Translation mode: {mode}, Detected language: {detected_lang}")

            # 日本語モードの場合は翻訳不要
            if mode == 'ja':
                print("Japanese mode - no translation needed")
                return text

            # 翻訳方向の決定
            target_lang = None

            # 英語モード
            if mode == 'en':
                if detected_lang == 'ja':
                    target_lang = 'en'  # 日本語→英語
                elif detected_lang == 'en':
                    target_lang = 'ja'  # 英語→日本語

            # 中国語モード
            elif mode == 'zh':
                if detected_lang == 'ja':
                    target_lang = 'zh'  # 日本語→中国語
                elif detected_lang == 'zh':
                    target_lang = 'ja'  # 中国語→日本語

            if target_lang is None:
                print(f"Unsupported language combination: mode={mode}, detected_lang={detected_lang}")
                return None

            print(f"Translation direction: {detected_lang} -> {target_lang}")

            # システムプロンプトを設定
            system_prompt = f"You are a professional translator. Translate the following text from {detected_lang} to {target_lang}. Provide only the translation, without any additional text."
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.7,
                max_tokens=150,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )

            translated_text = response.choices[0].message.content.strip()
            print(f"Translation result: {translated_text}")
            return translated_text

        except Exception as e:
            print(f"Translation error: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def _get_tts_lang(self, detected_lang: str, mode: str) -> str:
        """音声合成用の言語コードを取得"""
        print(f"Getting TTS language for detected_lang={detected_lang}, mode={mode}")
        
        # 日本語モード
        if mode == 'ja':
            return 'ja-JP'
        
        # 英語モード
        if mode == 'en':
            if detected_lang == 'ja':
                return 'en-US'  # 日本語の入力を英語に変換
            else:
                return 'ja-JP'  # 英語の入力を日本語に変換
        
        # 中国語モード
        if mode == 'zh':
            if detected_lang == 'ja':
                return 'zh-CN'  # 日本語の入力を中国語に変換
            else:
                return 'ja-JP'  # 中国語の入力を日本語に変換
        
        print(f"Warning: Falling back to default language (ja-JP) for mode={mode}")
        return 'ja-JP'  # デフォルト

    async def _send_translation(self, text: str, detected_lang: str, client_id: str, mode: str):
        """翻訳結果を送信"""
        if client_id not in self.active_connections:
            return
            
        websocket = self.active_connections[client_id]
        
        try:
            # 翻訳を実行
            translated_text = await self._translate_text(text, detected_lang, mode)
            if translated_text is None:
                print("[ERROR] Translation failed or not needed")
                return

            print(f"[DEBUG] Mode: {mode}")
            print(f"[DEBUG] Original text: {text}")
            print(f"[DEBUG] Translated text: {translated_text}")
            
            # 音声合成用の言語を取得
            tts_lang = self._get_tts_lang(detected_lang, mode)
            print(f"[DEBUG] Using TTS with language: {tts_lang}")

            # TTSサービスを使用して音声を生成
            audio_path = await self.tts_service.text_to_speech(translated_text, tts_lang.split('-')[0])
            print(f"[DEBUG] Generated audio path: {audio_path}")
            
            try:
                await websocket.send_json({
                    "type": "translation",
                    "text": translated_text,
                    "audioUrl": audio_path,
                    "sourceText": text
                })
            except Exception as e:
                print(f"[ERROR] WebSocket send error: {str(e)}")
                print(f"[ERROR] Error type: {type(e)}")
                if not isinstance(e, starlette.websockets.WebSocketDisconnect):
                    raise
                    
        except Exception as e:
            print(f"[ERROR] Translation process error: {str(e)}")
            print(f"[ERROR] Error type: {type(e)}")
            import traceback
            print(traceback.format_exc())

interpreter_service = InterpreterService() 