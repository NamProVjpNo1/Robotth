from machine import UART
import urequests
import json
import time
import network

# Kết nối WiFi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect('Quan Anh', '01669799620')

print("Đang kết nối WiFi...")
while not wifi.isconnected():
    time.sleep(1)
print('WiFi connected, IP:', wifi.ifconfig())

# UART2 cho GPS (TX=17, RX=16)
uart = UART(2, baudrate=9600, tx=17, rx=16)

# ham chuyen doi
def nmea_to_decimal(raw, direction):
    try:
        raw = float(raw)
        degrees = int(raw) // 100
        minutes = raw - (degrees * 100)
        decimal = degrees + minutes / 60
        if direction in ['S', 'W']:
            decimal = -decimal
        return decimal
    except:
        return None

# gui du lieu
def send_gps_to_server(latitude, longitude):
    url = "http://192.168.1.15/php/ESP32CAM/coordinates.php"
    data = {
        "latitude": latitude,
        "longitude": longitude
    }
    try:
        response = urequests.post(url, json=data)
        print("Server response:", response.text)
        response.close()
    except Exception as e:
        print("Error sending GPS:", e)

while True:
    if uart.any():
        line = uart.readline()
        try:
            line = line.decode('utf-8').strip()
            print(line)

            if line.startswith('$GPRMC'):
                parts = line.split(',')
                if parts[2] == 'A':
                    lat = nmea_to_decimal(parts[3], parts[4])
                    lon = nmea_to_decimal(parts[5], parts[6])
                    if lat is not None and lon is not None:
                        print("Toạ độ:", lat, lon)
                        send_gps_to_server(lat, lon)
        except:
            pass
    time.sleep(1)
