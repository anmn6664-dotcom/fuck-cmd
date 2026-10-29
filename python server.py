import asyncio
import json
import websockets
import os  # ফাইলের একদম উপরে এটি ইম্পোর্ট করে নেবেন

# কানেক্টড ক্লায়েন্ট এবং ড্যাশবোর্ড স্টোর করার ডিকশনারি
clients = {}      # Target/ESP32 Clients
dashboards = {}   # Web Dashboards

async def relay_handler(websocket, path):
    client_type = None
    client_id = None
    try:
        async for message in websocket:
            # যদি ডেটা বাইনারি বা টেক্সট স্ট্রিং হয় (যেমন ব্রাউজার থেকে সরাসরি পাথ পাঠানো হয়)
            if isinstance(message, str) and message.startswith('/'):
                # লোকাল নেটওয়ার্ক বা ডাইরেক্ট রাউটিংয়ের ক্ষেত্রে কমান্ড ব্রডকাস্ট বা হ্যান্ডেল করা
                print(f"Received Command/Path: {message}")
                continue

            try:
                data = json.loads(message)
                action = data.get("action")

                # ক্লায়েন্ট পিসি/ESP32 রেজিস্ট্রেশন
                if action == "register_client":
                    client_id = data.get("client_id")
                    clients[client_id] = websocket
                    print(f"[CONNECTED] Target Client: {client_id}")

                # ড্যাশবোর্ড রেজিস্ট্রেশন
                elif action == "register_dashboard":
                    client_id = data.get("client_id")
                    dashboards[client_id] = websocket
                    print(f"[CONNECTED] Dashboard for Client: {client_id}")

                # ড্যাশবোর্ড থেকে কমান্ড টার্গেট ক্লায়েন্টে পাঠানো
                elif action == "command":
                    target_id = data.get("client_id")
                    if target_id in clients:
                        await clients[target_id].send(json.dumps(data["payload"]))

                # টার্গেট ক্লায়েন্ট থেকে আউটপুট ড্যাশবোর্ডে পাঠানো
                elif action == "output":
                    target_id = data.get("client_id")
                    if target_id in dashboards:
                        await dashboards[target_id].send(json.dumps(data["payload"]))

            except json.JSONDecodeError:
                # যদি প্লেন টেক্সট বা অন্য কোনো রাফ স্ট্রিং কমান্ড আসে
                print(f"Raw Message Received: {message}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # ডিসকানেক্ট হলে লিস্ট থেকে রিমুভ করা
        if client_id:
            clients.pop(client_id, None)
            dashboards.pop(client_id, None)
            print(f"[DISCONNECTED] Client ID: {client_id}")



async def main():
    # Render-এর দেওয়া পোর্ট রিড করবে, না পেলে ডিফল্ট ৮০৮০ ব্যবহার করবে
    server_port = int(os.environ.get("PORT", 8080))
    async with websockets.serve(relay_handler, "0.0.0.0", server_port):
        print(f"🚀 High-Performance WebSocket Relay Server running on port {server_port}...")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped manually.")