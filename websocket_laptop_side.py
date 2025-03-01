import asyncio
import websockets

async def receive_telemetry():
    """Connects to the WebSocket server and prints telemetry data."""
    uri = "ws://192.168.2.2:5003"  # Replace with your TI board's actual IP

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {uri}")

        try:
            while True:
                message = await websocket.recv()
                print(f"Received telemetry: {message}")

        except websockets.ConnectionClosed:
            print("Connection closed")

if __name__ == "__main__":
    asyncio.run(receive_telemetry())
