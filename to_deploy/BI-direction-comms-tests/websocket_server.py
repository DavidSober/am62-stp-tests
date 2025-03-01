import asyncio
import websockets
import json
import random

async def send_telemetry(websocket, path):
    """Send random telemetry data to the client every second."""
    while True:
        telemetry_data = {
            "latency": round(random.uniform(50, 200), 2),
            "battery": round(random.uniform(30, 100), 1),
            "status": "OK" if random.random() > 0.1 else "WARNING"
        }
        await websocket.send(json.dumps(telemetry_data))
        await asyncio.sleep(1)  # Send updates every second

start_server = websockets.serve(send_telemetry, "0.0.0.0", 5003)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
