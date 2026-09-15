import asyncio
import websockets
import os

async def handle_twilio_stream(websocket):
    print("🔗 Client connected!")
    try:
        async for message in websocket:
            print(f"📩 Received: {message[:100]}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("🔌 Client disconnected")
    except Exception as e:
        print(f"❌ Handler error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 WebSocket server running on port {port}")
    async with websockets.serve(handle_twilio_stream, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())