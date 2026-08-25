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
    """Return TwiML to start Media Stream."""
    resp = VoiceResponse()
    stream = Stream(url=f"wss://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/media-stream")
    resp.append(stream)
    return Response(content=str(resp), media_type="text/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle Twilio Media Streams and bridge to Gemini Live."""
    await websocket.accept()
    print("🔗 Twilio WebSocket connected")

    try:
        async with websockets.connect(GEMINI_LIVE_URL) as gemini_ws:
            print("✅ Connected to Gemini Live")

            # Send setup to Gemini
            await gemini_ws.send(json.dumps({
                "setup": {
                    "model": "gemini-3.1-flash-live-preview",
                    "generation_config": {
                        "response_modalities": ["AUDIO"]
                    }
                }
            }))
            print("📤 Sent Gemini setup")

            # Main loop
            while True:
                try:
                    # Receive from Twilio
                    message = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                    data = json.loads(message)
                    event = data.get("event")

                    if event == "start":
                        print("📞 Call started")
                    elif event == "media":
                        # Forward audio to Gemini
                        await gemini_ws.send(json.dumps({
                            "realtime_input": {
                                "media_chunks": [{
                                    "data": data["media"]["payload"],
                                    "mime_type": "audio/pcm"
                                }]
                            }
                        }))
                    elif event == "stop":
                        print("📞 Call ended")
                        break

                    # Receive from Gemini and send to Twilio
                    try:
                        gemini_response = await asyncio.wait_for(gemini_ws.recv(), timeout=0.1)
                        gemini_data = json.loads(gemini_response)
                        if "audio" in gemini_data:
                            await websocket.send_text(json.dumps({
                                "event": "media",
                                "media": {"payload": gemini_data["audio"]}
                            }))
                    except asyncio.TimeoutError:
                        continue

                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Gemini WebSocket disconnected")
                    break

    except WebSocketDisconnect:
        print("🔌 Twilio WebSocket disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")