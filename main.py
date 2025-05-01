# main.py
from flask import Flask, request, jsonify, render_template
import asyncio
import websockets

app = Flask(__name__)
WS_URI = "ws://192.168.65.195:8765"  # Replace with your Pi's IP


# HTML Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/services.html')
def services():
    return render_template('services.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/manual.html')
def manual():
    return render_template('manual.html')

@app.route('/video_feed')
def video_feed():
    # Stream video frames
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/gesture.html')
def gesture():
    return render_template('gesture.html')


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