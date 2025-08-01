import cv2
from picamera2 import Picamera2
from datetime import datetime

class ManualCamera:
    def __init__(self):
        # Initialize camera
        self.picam2 = Picamera2()
        self.picam2.configure(self.picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
        self.picam2.start()
        self.capture_flag = False

    def capture_image(self):
        self.capture_flag = True
        
    def get_frame(self):
        frame = self.picam2.capture_array()
        
        # Capture photo when flag is set
        if self.capture_flag:
            filename = f"/home/CYBRO/Akshar/PHOTOS/capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Image saved: {filename}")
            self.capture_flag = False
            
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()
        
    def cleanup(self):
        self.picam2.stop()
