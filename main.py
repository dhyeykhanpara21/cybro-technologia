# main.py
from flask import Flask, request, jsonify, render_template
import asyncio
import websockets

app = Flask(__name__)
WS_URI = "ws://192.168.65.195:8765"  # Replace with your Pi's IP

# Serve the manual.html page
@app.route("/")
def index():
    return render_template("manual.html")

# Async function to send WebSocket messages
async def send_ws_message(message):
    try:
        async with websockets.connect(WS_URI) as websocket:
            await websocket.send(message)
            return "Message sent"
    except Exception as e:
        return f"Failed to send message: {str(e)}"

# Route to handle key press from the frontend
@app.route("/key-pressed", methods=["POST"])
def key_pressed():
    data = request.get_json()
    key = data.get("key")
    print(f"Key pressed: {key}")
    
    # Send the key to Raspberry Pi
    result = asyncio.run(send_ws_message(key))
    return jsonify({"status": result})
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)