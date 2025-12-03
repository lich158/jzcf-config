from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# 保存所有连接的 App WebSocket
active_connections = set()

@app.websocket("/ws/app")
async def websocket_app(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    print("App connected:", websocket.client)

    try:
        while True:
            data = await websocket.receive_text()
            print("Received from app:", data)
    except WebSocketDisconnect:
        print("App disconnected:", websocket.client)
        active_connections.remove(websocket)

# 网页：简单输入框 + 按钮（用于演示）
html = """
<!DOCTYPE html>
<html>
<body>
<h2>发送内容到所有App</h2>
<input id="msg" style="width:300px" placeholder="输入要发送的内容"/>
<button onclick="send()">发送</button>

<script>
function send(){
    fetch('/send', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ msg: document.getElementById('msg').value })
    })
    .then(r => r.text())
    .then(alert)
}
</script>

</body>
</html>
"""

@app.get("/")
async def index():
    return HTMLResponse(html)

# 接收来自网页的修改，并广播给所有 App
@app.post("/send")
async def send_to_app(request: Request):
    body = await request.json()
    msg = body.get("msg")

    # 广播逻辑
    removed_clients = []
    for ws in active_connections:
        try:
            await ws.send_text(json.dumps({
                "type": "update",
                "data": msg
            }))
        except Exception:
            removed_clients.append(ws)

    # 移除断开的客户端
    for ws in removed_clients:
        active_connections.remove(ws)

    return "已发送给在线App数量：" + str(len(active_connections))

