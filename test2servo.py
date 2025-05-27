from machine import Pin, PWM
import time

# Khởi tạo servo 1 trên GPIO 19, servo 2 trên GPIO 18 (đổi GPIO nếu cần)
servo1 = PWM(Pin(19), freq=50)
servo2 = PWM(Pin(18), freq=50)


while True:
    servo2.duty(26)
    time.sleep(3)
    servo2.duty(77)
    time.sleep(3)
    servo2.duty(123)
    time.sleep(3)