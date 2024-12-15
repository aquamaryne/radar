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
    
    distance = (end - start) * 34300 / 2   
    return max(2, min(distance, 400))   


def set_angle(angle):
    duty_cycle = 2 + (angle / 18)
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.1)


def radar_scan():
    plt.ion()   
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')   
    ax.set_theta_direction(-1)    
    ax.set_thetamin(0)
    ax.set_thetamax(180)

    angles = []
    distances = []

    try:
        while True:
            angles.clear()
            distances.clear()

            for angle in range(0, 181, 5):    
                set_angle(angle)
                distance = measure_distance()
                print(f"Угол: {angle}°, Расстояние: {distance:.2f} см")
                angles.append(np.radians(angle))
                distances.append(distance)

            ax.clear()
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)
            ax.set_thetamin(0)
            ax.set_thetamax(180)
            ax.plot(angles, distances, linestyle='-', marker='o', color='white', markersize=5)
            ax.set_facecolor('#004545')  
            plt.draw()
            plt.pause(0.01)

    except KeyboardInterrupt:
        print("Остановка радара...")
        servo.stop()
        GPIO.cleanup()

    plt.ioff()
    plt.show()


if __name__ == "__main__":
    radar_scan()