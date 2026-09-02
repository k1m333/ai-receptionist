import asyncio
import websockets

async def handle_twilio_stream(websocket, path):
    print("🔗 Twilio WebSocket connected!")
    try:
        async for message in websocket:
            print(f"📩 Received: {message[:100]}")
            # Echo back a test message to keep the connection alive
            await websocket.send('{"test": "pong"}')
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

async def main():
    async with websockets.serve(handle_twilio_stream, "0.0.0.0", 8765):
        print("🚀 WebSocket server running on port 8765")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())