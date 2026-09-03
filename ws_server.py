import asyncio
import websockets
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def handle_twilio_stream(websocket, path):
    """Bridge Twilio Media Streams to OpenAI Realtime API."""
    print("🔗 Twilio WebSocket connected!")
    
    try:
        # Connect to OpenAI Realtime
        async with websockets.connect(
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2025-12-17",
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
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
            
            # Bridge messages between Twilio and OpenAI
            while True:
                # Receive from Twilio
                message = await websocket.recv()
                data = json.loads(message)
                
                if data.get("event") == "media":
                    audio = data["media"]["payload"]
                    await openai_ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": audio
                    }))
                
                # Receive from OpenAI and send to Twilio
                try:
                    openai_msg = await asyncio.wait_for(openai_ws.recv(), timeout=0.1)
                    openai_data = json.loads(openai_msg)
                    if "audio" in openai_data:
                        await websocket.send(json.dumps({
                            "event": "media",
                            "media": {"payload": openai_data["audio"]}
                        }))
                except asyncio.TimeoutError:
                    continue
                    
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 WebSocket server running on port {port}")
    async with websockets.serve(handle_twilio_stream, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())