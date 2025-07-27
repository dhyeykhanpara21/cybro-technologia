import time

import board

import busio

import RPi.GPIO as GPIO

from adafruit_pca9685 import PCA9685

import asyncio

import websockets



# ======= GEAR MOTOR SETUP =======

IN1, IN2, IN3, IN4, ENA, ENB = 17, 27, 22, 23, 18, 24

GPIO.setmode(GPIO.BCM)

GPIO.setwarnings(False)

GPIO.setup([IN1, IN2, IN3, IN4, ENA, ENB], GPIO.OUT)

pwmA = GPIO.PWM(ENA, 1000)

pwmB = GPIO.PWM(ENB, 1000)



# Start with medium speed

motor_speed = 70  # percentage

pwmA.start(motor_speed)

pwmB.start(motor_speed)



def update_motor_speed(speed_percent):

    pwmA.ChangeDutyCycle(speed_percent)

    pwmB.ChangeDutyCycle(speed_percent)



def move_forward():

    GPIO.output(IN1, GPIO.HIGH)

    GPIO.output(IN2, GPIO.LOW)

    GPIO.output(IN3, GPIO.HIGH)

    GPIO.output(IN4, GPIO.LOW)



def move_backward():

    GPIO.output(IN1, GPIO.LOW)

    GPIO.output(IN2, GPIO.HIGH)

    GPIO.output(IN3, GPIO.LOW)

    GPIO.output(IN4, GPIO.HIGH)



def left_forward_right_backward():

    GPIO.output(IN1, GPIO.HIGH)

    GPIO.output(IN2, GPIO.LOW)

    GPIO.output(IN3, GPIO.LOW)

    GPIO.output(IN4, GPIO.HIGH)



def left_backward_right_forward():

    GPIO.output(IN1, GPIO.LOW)

    GPIO.output(IN2, GPIO.HIGH)

    GPIO.output(IN3, GPIO.HIGH)

    GPIO.output(IN4, GPIO.LOW)



def stop_motors():

    GPIO.output(IN1, GPIO.LOW)

    GPIO.output(IN2, GPIO.LOW)

    GPIO.output(IN3, GPIO.LOW)

    GPIO.output(IN4, GPIO.LOW)



# ======= SERVO SETUP =======

i2c = busio.I2C(board.SCL, board.SDA)

pwm = PCA9685(i2c)

pwm.frequency = 50

SERVO_MIN = 2000

SERVO_MAX = 8000



def angle_to_duty(angle):

    return int(SERVO_MIN + (angle / 180.0) * (SERVO_MAX - SERVO_MIN))



SERVO_CHANNEL_MAP = {

    'top_left': 3,

    'top_right': 12,

    'mid_left': 1,

    'mid_right': 14,

    'bot_left': 0,

    'bot_right': 15,

    'shoulder': 11,

    'elbow': 9,

    'grip': 8,

    'camera_right_left': 6,

    'camera_up_down': 7

}



servo_angles = {

    'camera_right_left': 90,

    'camera_up_down': 90,

    'shoulder': 90,  # Initialize shoulder servo

    'elbow': 90,    # Initialize elbow servo

    'grip': 90      # Initialize grip servo

}



def set_single_servo(name, delta):

    if name in servo_angles:

        servo_angles[name] = max(0, min(180, servo_angles[name] + delta))

        channel = SERVO_CHANNEL_MAP[name]

        pwm.channels[channel].duty_cycle = angle_to_duty(servo_angles[name])



WHEEL_CHANNELS = [

    SERVO_CHANNEL_MAP['top_left'],

    SERVO_CHANNEL_MAP['top_right'],

    SERVO_CHANNEL_MAP['mid_left'],

    SERVO_CHANNEL_MAP['mid_right'],

    SERVO_CHANNEL_MAP['bot_left'],

    SERVO_CHANNEL_MAP['bot_right']

]



def set_wheel_angles(angles):

    for idx, channel in enumerate(WHEEL_CHANNELS):

        angle = max(0, min(180, angles[idx]))

        pwm.channels[channel].duty_cycle = angle_to_duty(angle)



movements = {

    'w': ([90] * 6, move_forward),

    's': ([90] * 6, move_backward),

    'a': ([40, 40, 40, 140, 140, 140], left_backward_right_forward),

    'd': ([140, 140, 140, 40, 40, 40], left_forward_right_backward),

    'q': ([87, 87, 87, 93, 93, 93], move_forward),

    'e': ([93, 93, 93, 87, 87, 87], move_forward),

    'z': ([60, 60, 60, 120, 120, 120], move_forward),

    'c': ([120, 120, 120, 60, 60, 60], move_forward),

    'r': ([50, 50, 50, 130, 130, 130], left_forward_right_backward),

    'l': ([130, 130, 130, 50, 50, 50], left_backward_right_forward),

    'u': ([85, 85, 85, 95, 95, 95], move_forward),

    'i': ([95, 95, 95, 85, 85, 85], move_forward),

    'j': ([85, 85, 85, 95, 95, 95], move_backward),

    'k': ([95, 95, 95, 85, 85, 85], move_backward)

}



async def handle_command(command):

    # Parse the command and execute the appropriate function

    if command in movements:

        angles, motor_action = movements[command]

        set_wheel_angles(angles)

        motor_action()

    elif command == 'x' or command == ' ':

        stop_motors()

    elif command == '1':

        motor_speed = 40

        update_motor_speed(motor_speed)

    elif command == '2':

        motor_speed = 70

        update_motor_speed(motor_speed)

    elif command == '3':

        motor_speed = 100

        update_motor_speed(motor_speed)

    elif command == 't':

        set_single_servo('shoulder', +5)

    elif command == 'y':

        set_single_servo('shoulder', -5)

    elif command == 'g':

        set_single_servo('elbow', +5)

    elif command == 'h':

        set_single_servo('elbow', -5)

    elif command == 'o':

        set_single_servo('grip', +5)

    elif command == 'm':

        set_single_servo('grip', -5)

    elif command == 'up':

        set_single_servo('camera_up_down', +5)

    elif command == 'down':

        set_single_servo('camera_up_down', -5)

    elif command == 'right':

        set_single_servo('camera_right_left', +5)

    elif command == 'left':

        set_single_servo('camera_right_left', -5)



connected_clients = set()



async def websocket_handler(websocket):

    print("Client connected")

    connected_clients.add(websocket)

    try:

        async for message in websocket:

            print(f"Received from Flask: {message}")

            await handle_command(message)  # Send command to rover

    except websockets.exceptions.ConnectionClosed:

        print("Client disconnected")

    finally:

        connected_clients.remove(websocket)



async def main():

    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):

        print("WebSocket server running on ws://0.0.0.0:8765")

        await asyncio.Future()  # run forever



if __name__ == "__main__":

    try:

        asyncio.run(main())

    except Exception as e:

        print(f"An error occurred: {e}")

    finally:

        # Clean up GPIO

        GPIO.cleanup()

