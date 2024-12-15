import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt
import numpy as np

TRIG = 23
ECHO = 24
SERVO_PIN = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(SERVO_PIN, GPIO.OUT)

servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

def measure_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    while GPIO.input(ECHO) == 0:
        start = time.time()
    while GPIO.input(ECHO) == 1:
        end = time.time()
    return round((end - start) * 34300 / 2, 2)

def set_angle(angle):
    duty = 2 + (angle / 18)
    servo.ChangeDutyCycle(duty)
    time.sleep(0.3)

def scan_and_visualize():
    angles = []
    distances = []
    for angle in range(0, 181, 5):  
        set_angle(angle)
        distance = measure_distance()
        print(f"Угол: {angle}, Расстояние: {distance} см")
        distances.append(distance)
        angles.append(angle)

    plt.figure(figsize=(8, 4))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.plot(np.radians(angles), distances, marker='o', linestyle='-', color='white')
    ax.set_facecolor('#004545')
    plt.show()

try:
    while True:
        scan_and_visualize()
except KeyboardInterrupt:
    print("Остановка радара...")
    servo.stop()
    GPIO.cleanup()
