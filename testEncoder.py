from machine import Pin
import urequests
import time
import network
import math

SSID = 'KGU 3'
PASSWORD = ''
SERVER_URL = "http://localhost/php/ESP32CAM/distance.php"

PPR = 20 
WHEEL_DIAMETER = 0.065
WHEEL_CIRCUMFERENCE = math.pi * WHEEL_DIAMETER  # Chu vi bánh xe (m)

# Biến toàn cục đếm xung
pulse_count_left = 0
pulse_count_right = 0

# Xử lý ngắt
def handle_left(pin):
    global pulse_count_left
    pulse_count_left += 1

def handle_right(pin):
    global pulse_count_right
    pulse_count_right += 1

# Cài đặt chân encoder
pin_left = Pin(2, Pin.IN)
pin_right = Pin(4, Pin.IN)
pin_left.irq(trigger=Pin.IRQ_RISING, handler=handle_left)
pin_right.irq(trigger=Pin.IRQ_RISING, handler=handle_right)

# Kết nối WiFi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Đang kết nối WiFi...")
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("Đã kết nối WiFi:", wlan.ifconfig())

def calculate_distance(left, right):
    avg_pulse = (left + right) / 2
    distance = (avg_pulse / PPR) * WHEEL_CIRCUMFERENCE
    return distance

def send_encoder_data(distance):
    try:
        data = {
            "distance": distance
        }
        response = urequests.post(SERVER_URL, json=data)
        print("Đã gửi:", response.text)
        response.close()
    except Exception as e:
        print("Lỗi gửi dữ liệu:", e)

# Main
connect_wifi(SSID, PASSWORD)
INTERVAL = 5  # giây

while True:
    time.sleep(INTERVAL)
    print("Xung trái:", pulse_count_left, "| Xung phải:", pulse_count_right)

    distance, speed = calculate_distance_speed(pulse_count_left, pulse_count_right, INTERVAL)
    print("Quãng đường:", round(distance, 3), "m | Vận tốc:", round(speed, 3), "m/s")

    send_encoder_data(pulse_count_left, pulse_count_right, distance, speed)

    pulse_count_left = 0
    pulse_count_right = 0
