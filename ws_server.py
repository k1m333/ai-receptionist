import asyncio
import json
import os
import websockets

async def handle_twilio_stream(websocket):
    print("🔗 Twilio WebSocket connected!")
    
    try:
        # Send a welcome message to Twilio
        await websocket.send(json.dumps({
            "event": "media",
            "media": {"payload": "SGVsbG8gZnJvbSBBSSBSZWNlcHRpb25pc3Qh"}  # "Hello from AI Receptionist!" in base64
        }))
        
        # Echo any received messages
        async for message in websocket:
            print(f"📩 Received from Twilio: {message[:100]}")
            # Echo back a test response
            await websocket.send(json.dumps({
                "event": "media",
                "media": {"payload": "RXhjZWxsZW50ISBZb3UgY29ubmVjdGVkIQ=="}  # "Excellent! You connected!"
            }))
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 WebSocket server running on port {port}")
    async with websockets.serve(handle_twilio_stream, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())