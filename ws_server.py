import asyncio
import json
import os
import websockets
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime"

async def handle_twilio_stream(websocket):
    print("🔗 Twilio client connected!")
    
    try:
        # Connect to OpenAI Realtime
        print("🔄 Connecting to OpenAI Realtime...")
        async with websockets.connect(
            OPENAI_URL
        ) as openai_ws:
            print("✅ Connected to OpenAI Realtime!")
            
            # Send session config
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "instructions": "You are a helpful AI receptionist.",
                    "audio": {
                    "input": {
                        "format": { "type": "audio/pcm", "rate": 24000 }
                    },
                    "output": {
                        "format": { "type": "audio/pcm", "rate": 24000 },
                        "voice": "alloy"
                    }
                    }
                }
            }))
            print("📤 Session config sent")
            
            # Bridge messages
            while True:
                try:
                    # Receive from Twilio
                    twilio_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    print(f"📩 Twilio: {twilio_msg[:80]}...")
                    
                    try:
                        twilio_data = json.loads(twilio_msg)
                        if twilio_data.get("event") == "media":
                            audio = twilio_data["media"]["payload"]
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": audio
                            }))
                            print("🎵 Sent audio to OpenAI")
                    except json.JSONDecodeError:
                        print("📩 Non-JSON message from Twilio (test client)")
                        
                except asyncio.TimeoutError:
                    print("⏳ No Twilio message in 5s")
                    
                # Receive from OpenAI
                try:
                    openai_msg = await asyncio.wait_for(openai_ws.recv(), timeout=0.1)
                    openai_data = json.loads(openai_msg)
                    print(f"📥 OpenAI event: {openai_data.get('type')}")
                    
                    if openai_data.get("type") == "response.audio.delta":
                        audio = openai_data.get("delta", "")
                        if audio:
                            await websocket.send(json.dumps({
                                "event": "media",
                                "media": {"payload": audio}
                            }))
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"❌ OpenAI recv error: {e}")
                    break
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 WebSocket server running on port {port}")
    async with websockets.serve(handle_twilio_stream, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())