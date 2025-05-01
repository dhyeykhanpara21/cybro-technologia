# main.py
from flask import Flask, request, jsonify, render_template
import asyncio
import websockets
import cv2
import mediapipe as mp
import time

import socket
import time
import logging
import subprocess
import os
import sys
from typing import Dict, Any

from flask import Flask,Response, render_template, request, jsonify
from flask_cors import CORS

import cv2
import mediapipe as mp
import time

app = Flask(__name__)
CORS(app)
WS_URI = "ws://192.168.65.195:8765"  # Replace with your Pi's IP

# Raspberry Pi connection details
RPI_HOST = '192.168.1.100'  # Replace with your Raspberry Pi's IP address
RPI_PORT = 22  # SSH port or any other open port on your Pi

# Connection status
rpi_status = {
    "connected": False,
    "last_check": None,
    "error": None
}

def check_rpi_connection():
    """Check if the Raspberry Pi is reachable using a simple socket connection"""
    global rpi_status
    
    try:
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)  # Set a timeout of 3 seconds
        
        # Attempt to connect to the Raspberry Pi
        result = s.connect_ex((RPI_HOST, RPI_PORT))
        s.close()
        
        # If result is 0, the connection was successful
        if result == 0:
            rpi_status["connected"] = True
            rpi_status["last_check"] = time.time()
            rpi_status["error"] = None
            logger.info(f"Successfully connected to Raspberry Pi at {RPI_HOST}")
        else:
            rpi_status["connected"] = False
            rpi_status["last_check"] = time.time()
            rpi_status["error"] = f"Connection failed with error code: {result}"
            logger.error(f"Failed to connect to Raspberry Pi: Error code {result}")
            
    except socket.error as e:
        rpi_status["connected"] = False
        rpi_status["last_check"] = time.time()
        rpi_status["error"] = str(e)
        logger.error(f"Failed to connect to Raspberry Pi: {e}")

def execute_script(script_path: str, arguments: list = None, timeout: int = 60) -> Dict[str, Any]:
    """
    Execute a script at the given path with optional arguments
    
    Args:
        script_path: Path to the script to execute
        arguments: List of arguments to pass to the script
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary containing execution results
    """
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return {
            "success": False,
            "error": f"Script not found: {script_path}",
            "output": None,
            "return_code": None
        }
    
    # Prepare the command
    cmd = [script_path]
    if arguments:
        cmd.extend(arguments)
    
    logger.info(f"Executing script: {' '.join(cmd)}")
    
    try:
        # Execute the script
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return_code = process.returncode
            
            if return_code == 0:
                logger.info(f"Script executed successfully: {script_path}")
                return {
                    "success": True,
                    "output": stdout,
                    "error": stderr if stderr else None,
                    "return_code": return_code
                }
            else:
                logger.warning(f"Script execution failed with code {return_code}: {script_path}")
                return {
                    "success": False,
                    "output": stdout,
                    "error": stderr,
                    "return_code": return_code
                }
                
        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(f"Script execution timed out after {timeout} seconds: {script_path}")
            return {
                "success": False,
                "error": f"Execution timed out after {timeout} seconds",
                "output": None,
                "return_code": None
            }
            
    except Exception as e:
        logger.error(f"Error executing script {script_path}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "output": None,
            "return_code": None
        }




# ====== MEDIA PIPELINE SETUP ======
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# ====== VIDEO CAPTURE ======
cap = cv2.VideoCapture(0)
prev_actions = [None, None]
last_action_times = [0, 0]


# ====== VALID GESTURES ======
VALID_GESTURES = {
    (0,0,0,0,0): 'forward',
    (0,1,1,0,0): 'backward',
    (0,1,1,1,0): 'tank_left',
    (0,1,1,1,1): 'tank_right',
    (1,1,1,1,1): 'stop',
    (1,0,0,0,1): 'crab_right',
    (0,1,0,0,1): 'rotate_cw',
    (0,1,1,0,1): 'rotate_ccw',
    (0,1,0,1,0): 'fwd_left',
    (0,1,0,1,1): 'fwd_right',
    (0,1,1,0,0): 'bwd_left',
    (0,1,1,0,1): 'bwd_right',
    (1,1,0,0,0): 'soft_left',
    (1,1,1,0,0): 'soft_right'
}

# Recognize a gesture based on hand landmarks
def recognize_gesture(hand_landmarks):
    tip_ids = [4, 8, 12, 16, 20]
    fingers = [0] * 5
    # Thumb
    fingers[0] = 1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x else 0
    # Other four fingers
    for i in range(1, 5):
        fingers[i] = 1 if hand_landmarks.landmark[tip_ids[i]].y < hand_landmarks.landmark[tip_ids[i] - 2].y else 0
    return VALID_GESTURES.get(tuple(fingers), None)

# Generate video frames with gesture overlay
def generate_frames():
    global prev_actions, last_action_times

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)  # Flip horizontally to create mirror image
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        gesture_text = None
        if results.multi_hand_landmarks:
            for idx, landmarks in enumerate(results.multi_hand_landmarks):
                mp_drawing.draw_landmarks(frame, landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                gesture = recognize_gesture(landmarks)
                if gesture and (gesture != prev_actions[idx % 2] or time.time() - last_action_times[idx % 2] > 1):
                    prev_actions[idx % 2] = gesture
                    last_action_times[idx % 2] = time.time()
                    gesture_text = gesture

        # Overlay detected gesture text
        if gesture_text:
            cv2.putText(frame,
                        f"Detected: {gesture_text}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                        cv2.LINE_AA)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Yield frame in HTTP multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')



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

# ====== FLASK ROUTES ======
@app.route('/gesture.html')
def gesture():
    # Serve the HTML UI
    return render_template('gesture.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)