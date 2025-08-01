from flask import Flask, Response
from flask_cors import CORS
import cv2
from picamera2 import Picamera2
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

class PiCamera:
    def __init__(self):
        self.picam2 = Picamera2()
        # Update configuration to use RGB format
        self.picam2.configure(self.picam2.create_preview_configuration(main={"format": 'RGB888', "size": (640, 480)}))
        self.picam2.start()
        
    def get_frame(self):
        frame = self.picam2.capture_array()
        # Convert frame to BGR for OpenCV processing
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()

camera = PiCamera()

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)
