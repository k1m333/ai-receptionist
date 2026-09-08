import asyncio
import websockets
import os

async def handle_twilio_stream(websocket):
    print("🔗 WebSocket connection attempt")
    print(f"📋 Path: {websocket.path}")
    
    try:
        await websocket.accept()
        print("✅ WebSocket connection accepted!")
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"📩 Received: {message[:200]}...")
                
                # Send a test response
                await websocket.send('{"event": "media", "media": {"payload": "SGVsbG8gZnJvbSBBSSBSZWNlcHRpb25pc3Qh"}}')
                print("📤 Sent test audio response")
                
            except asyncio.TimeoutError:
                print("⏳ No message received, keeping connection alive")
            except websockets.exceptions.ConnectionClosed:
                print("🔌 Twilio disconnected")
                break
                
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