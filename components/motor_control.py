from machine import Pin
import time


class MotorControl:
    forward = True
    running_time = 0

    def __init__(self, motor_pin1, motor_pin2, forward=True):
        self.forward = forward
        self.motor_pin_1 = Pin(motor_pin1, Pin.OUT)  # IN1+6
        self.motor_pin_2 = Pin(motor_pin2, Pin.OUT)  # IN2

        self.motor_running = False

    def start_motor_up(self):
        self.forward = True
        self.rotate()

    def start_motor_down(self):
        self.forward = False
        self.rotate()

    def rotate(self):
        self.motor_pin_1.value(self.forward)
        self.motor_pin_2.value(not self.forward)
        self.motor_running = True
        self.running_time = time.ticks_ms()

    def stop_motor(self):
        self.motor_pin_1.value(0)
        self.motor_pin_2.value(0)
        self.motor_running = False

    def is_motor_running(self):
        return self.motor_running

    def get_running_time(self):
        if self.motor_running:
            return time.ticks_ms() - self.running_time
        return 0
