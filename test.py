from machine import Pin
import time

# Khai báo chân GPIO
trig = Pin(4, Pin.OUT)
echo = Pin(5, Pin.IN)

def dokhoangcach():
    trig.value(0)
    time.sleep_us(2)  # Đảm bảo tín hiệu sạch
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    while echo.value() == 0:
        pass
    start = time.ticks_us()

    while echo.value() == 1:
        pass
    end = time.ticks_us()

    # Tính khoảng cách (cm)
    duration = time.ticks_diff(end, start)
    distance = int((duration / 2) / 29.412)
    return distance

# Chạy thử
while True:
    print("Khoảng cách:", dokhoangcach(), "cm")
    time.sleep(1)
