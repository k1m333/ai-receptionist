import os
import json
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Stream
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

GEMINI_LIVE_URL = f"wss://generativelanguage.googleapis.com/ws/live/v1beta/models/gemini-3.1-flash-live-preview:live?key={os.getenv('GEMINI_API_KEY')}"

@app.post("/voice")
async def voice():
    resp = VoiceResponse()
    stream = Stream(url="wss://auto-ai-receptionist-websocket.onrender.com/media-stream")
    resp.append(stream)
    return Response(content=str(resp), media_type="text/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    print("🔗 Twilio WebSocket connected")

    try:
        # Wait for the first message (should be a 'start' event)
        data = await websocket.receive_text()
        print(f"📩 Received from Twilio: {data[:200]}...")

        # Send a simple acknowledgment to keep the connection alive
        await websocket.send_text('{"event": "connected"}')

        # Keep the connection open and listen for more messages
        while True:
            try:
                message = await websocket.receive_text()
                print(f"📩 Received from Twilio: {message[:100]}...")
                # You'll later add logic to forward this to Gemini
            except Exception as e:
                print(f"❌ Error receiving message: {e}")
                break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")

@app.websocket("/test")
async def test_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("WebSocket is working!")
    await websocket.close()
