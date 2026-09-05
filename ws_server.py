import asyncio
import json
import os
import websockets
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2025-12-17"

async def handle_twilio_stream(websocket):
    print("🔗 Twilio WebSocket connected!")
    
    try:
        # Wait for the first message (Twilio sends 'start' event)
        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(message)
        print(f"📩 First message from Twilio: {data.get('event')}")
        
        if data.get("event") != "start":
            print("❌ Expected 'start' event, got something else")
            return
        
        print("📞 Twilio call started")
        
        # Now connect to OpenAI
        print("🔄 Connecting to OpenAI Realtime...")
        async with websockets.connect(
            OPENAI_URL,
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            },
            timeout=10
        ) as openai_ws:
            print("✅ Connected to OpenAI Realtime API!")
            
            # Send session config
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": "You are a helpful AI receptionist. Be concise and friendly.",
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                }
            }))
            print("📤 Session config sent")
            
            # Main bridge loop
            while True:
                try:
                    # Receive from Twilio
                    twilio_msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    twilio_data = json.loads(twilio_msg)
                    
                    if twilio_data.get("event") == "media":
                        audio = twilio_data["media"]["payload"]
                        await openai_ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": audio
                        }))
                        print("🎵 Forwarded audio to OpenAI")
                    elif twilio_data.get("event") == "stop":
                        print("📞 Twilio call ended")
                        break
                        
                except asyncio.TimeoutError:
                    # No message from Twilio, check OpenAI
                    try:
                        openai_msg = await asyncio.wait_for(openai_ws.recv(), timeout=0.2)
                        openai_data = json.loads(openai_msg)
                        if openai_data.get("type") == "response.audio.delta":
                            audio = openai_data.get("delta", "")
                            if audio:
                                await websocket.send(json.dumps({
                                    "event": "media",
                                    "media": {"payload": audio}
                                }))
                                print("🎵 Forwarded audio to Twilio")
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"❌ OpenAI error: {e}")
                        break
                        
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for Twilio 'start' event")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 WebSocket server running on port {port}")
    async with websockets.serve(handle_twilio_stream, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())