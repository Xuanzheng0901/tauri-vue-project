import asyncio
import websockets
import json
import base64
from pathlib import Path

class CameraWebSocketServer:
    def __init__(self, host="127.0.0.1", port=8000, image_dir="images", frame_rate=1):
        self.host = host
        self.port = port
        self.image_dir = Path(image_dir)
        self.frame_delay = 1 / frame_rate
        self.image_files = self._load_images()

    def _load_images(self):
        extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif")
        files = []
        for ext in extensions:
            files.extend(self.image_dir.glob(f"*{ext}"))
        files = sorted(files)
        print(f"已加载 {len(files)} 张图片")
        return files

    async def handle_client(self, websocket):
        client_addr = websocket.remote_address
        print(f"客户端已连接: {client_addr}，开始发送图片")

        frame_count = 0

        try:
            while True:
                for image_path in self.image_files:
                    # 直接读取文件的二进制数据
                    image_bytes = image_path.read_bytes()

                    # 使用纯二进制发送代替 JSON 和 Base64 编码，极大地减小了体积并且速度飞快
                    await websocket.send(image_bytes)

                    # 随后立刻发送一个文本帧 (JSON)，携带该帧对应的识别数据
                    metadata = {
                        "type": "results",
                        "frame_id": frame_count,
                        "objects": {
                            "person": 2,
                            "car": 1
                        }
                    }
                    await websocket.send(json.dumps(metadata))

                    frame_count += 1

                    if frame_count % 10 == 0:
                        print(f"已发送 {frame_count} 帧 (当前: {image_path.name})")

                    await asyncio.sleep(self.frame_delay)

        except websockets.exceptions.ConnectionClosed:
            print(f"客户端已断开: {client_addr}，共发送 {frame_count} 帧")

    async def start(self):
        if not self.image_files:
            print(f"警告：目录 '{self.image_dir}' 中没有图��文件，请放入后再试。")
            # 即使没有图片也启动服务器，方便测试连接
            # return

        # 注意: 如果要运行，需升级为 websockets 10+ API 或使用最新版本
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"WebSocket服务器已启动: ws://{self.host}:{self.port}")
            print(f"图片目录: {self.image_dir.absolute()}")
            print("等待客户端连接...\n")
            await asyncio.Future()

async def main():
    server = CameraWebSocketServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    asyncio.run(main())
