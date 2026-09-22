import asyncio
import json
import os
import websockets
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime"

# VAD (Voice Activity Detection) settings
VAD_THRESHOLD = 0.5
PREFIX_PADDING_MS = 300
SILENCE_DURATION_MS = 500


async def handle_twilio_stream(websocket):
    print("🔗 Twilio client connected!")

    try:
        print("🔄 Connecting to OpenAI Realtime...")
        async with websockets.connect(
            OPENAI_URL,
            additional_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
        ) as openai_ws:
            print("✅ Connected to OpenAI Realtime!")

            # Session config with server-side VAD
            await openai_ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "instructions": (
                        "You are a helpful AI receptionist for an auto service center. "
                        "Be concise, friendly, and helpful. Answer questions about hours, "
                        "services, and pricing. Help callers book appointments."
                    ),
                    "audio": {
                        "input": {
                            "format": {"type": "g711_ulaw"},
                            "turn_detection": {
                                "type": "server_vad",
                                "threshold": VAD_THRESHOLD,
                                "prefix_padding_ms": PREFIX_PADDING_MS,
                                "silence_duration_ms": SILENCE_DURATION_MS,
                            },
                        },
                        "output": {
                            "format": {"type": "g711_ulaw"},
                            "voice": "alloy",
                        },
                    },
                }
            }))
            print("📤 Session config sent (g711_ulaw + server VAD)")

            # Task: Twilio → OpenAI
            async def twilio_to_openai():
                try:
                    async for twilio_msg in websocket:
                        try:
                            data = json.loads(twilio_msg)
                            if data.get("event") == "media":
                                audio = data["media"]["payload"]
                                await openai_ws.send(json.dumps({
                                    "type": "input_audio_buffer.append",
                                    "audio": audio
                                }))
                            elif data.get("event") == "stop":
                                print("📞 Twilio call ended")
                                await openai_ws.close()
                                return
                        except json.JSONDecodeError:
                            print("📩 Non-JSON message from Twilio")
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Twilio WebSocket closed")

            # Task: OpenAI → Twilio
            async def openai_to_twilio():
                try:
                    async for openai_msg in openai_ws:
                        try:
                            data = json.loads(openai_msg)
                            event_type = data.get("type")
                            print(f"📥 OpenAI event: {event_type}")

                            if event_type == "response.output_audio.delta":
                                audio = data.get("delta", "")
                                if audio:
                                    await websocket.send(json.dumps({
                                        "event": "media",
                                        "media": {"payload": audio}
                                    }))
                                    print("🎵 Forwarded AI audio to Twilio")
                            elif event_type == "response.done":
                                print("✅ AI response complete")
                            elif event_type == "error":
                                print(f"❌ OpenAI error: {data}")
                        except json.JSONDecodeError:
                            pass
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 OpenAI WebSocket closed")

            # Run both tasks concurrently
            await asyncio.gather(
                twilio_to_openai(),
                openai_to_twilio(),
            )

    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"🚀 WebSocket server running on port {port}")
    async with websockets.serve(
        handle_twilio_stream,
        "0.0.0.0",
        port,
        ping_interval=20,
        ping_timeout=20,
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())