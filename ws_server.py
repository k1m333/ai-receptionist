import asyncio
import websockets
import os

async def handler(websocket):  # ← removed 'path'
    print("🔗 Client connected!")
    try:
        async for message in websocket:
            print(f"📩 Received: {message[:100]}")
            await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("🔌 Client disconnected")

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 WebSocket server running on port {port}")
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())