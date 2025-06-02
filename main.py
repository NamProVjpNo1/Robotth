from machine import Pin, UART, PWM
import urequests
import json
import time
import network
import math

# WiFi config
ssid = 'Banh Mi'
wifi_pass = 'banhbao2022'
url_data = "http://192.168.1.5/php/ESP32CAM/photo.php"

# Ultrasonic sensor
trig = Pin(2, Pin.OUT)
echo = Pin(4, Pin.IN)
limited = 25

# Camera trigger (nếu cần)
triggercam = Pin(5, Pin.OUT)

# UART cho GPS
uart_gps = UART(2, baudrate=9600, tx=17, rx=16)

# Encoder
pulse_countL = 0
pulse_countR = 0
ppr = 20
wheel_dmt = 0.065
wheelC = math.pi * wheel_dmt

# Động cơ
in1 = Pin(12, Pin.OUT)
in2 = Pin(14, Pin.OUT)
in3 = Pin(27, Pin.OUT)
in4 = Pin(26, Pin.OUT)
ENA = PWM(Pin(13), freq=1000, duty=0)
ENB = PWM(Pin(25), freq=1000, duty=0)

# Servo
servo = PWM(Pin(15), freq=50, duty=77)
servoX = PWM(Pin(18), freq=50, duty=77)
servoY = PWM(Pin(19), freq=50, duty=77)

latitude = ""
longitude = ""

# Kết nối wifi
def conn_wifi(ssid, wifi_pass):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to wifi...")
        wlan.connect(ssid, wifi_pass)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("Wifi:", wlan.ifconfig(), "is connected")

# Chuyển đổi GPS NMEA sang thập phân
def nmea_to_decimal(raw, direction):
    try:
        raw = float(raw)
        degrees = int(raw) // 100
        minutes = raw - (degrees * 100)
        decimal = degrees + minutes / 60
        if direction in ['S', 'W']:
            decimal = -decimal
        return round(decimal, 6)
    except:
        return None

def read_gps():
    global latitude, longitude
    timeout = time.time() + 2
    while time.time() < timeout:
        if uart_gps.any():
            line = uart_gps.readline()
            try:
                line = line.decode('utf-8').strip()
                if line.startswith('$GPRMC'):
                    parts = line.split(',')
                    if parts[2] == 'A':
                        lat = nmea_to_decimal(parts[3], parts[4])
                        lon = nmea_to_decimal(parts[5], parts[6])
                        if lat is not None and lon is not None:
                            latitude = lat
                            longitude = lon
                            print("GPS:", latitude, longitude)
                            return
            except:
                pass

def send_data_to_server(distance):
    global latitude, longitude
    read_gps()
    time.sleep(5)
    print("Dữ liệu GPS gửi lên server: latitude =", latitude, ", longitude =", longitude)
    data = {
        "distance": distance,
        "latitude": latitude,
        "longitude": longitude
    }
    try:
        response = urequests.post(url_data, json=data)
        print("Server response:", response.text)
        response.close()
    except Exception as e:
        print("Error sending data:", e)

# Encoder count
def countPulseL(pin):
    global pulse_countL
    pulse_countL += 1

def countPulseR(pin):
    global pulse_countR
    pulse_countR += 1

lPinP = Pin(33, Pin.IN)
rPinP = Pin(32, Pin.IN)
lPinP.irq(trigger=Pin.IRQ_RISING, handler=countPulseL)
rPinP.irq(trigger=Pin.IRQ_RISING, handler=countPulseR)

# Điều khiển động cơ, đo khoảng cách, servo
def resetdongco():
    in1.value(0)
    in2.value(0)
    in3.value(0)
    in4.value(0)
    setSpeed(0, 0)

def setSpeed(leftSpeed, rightSpeed):
    leftSpeed = max(0, min(leftSpeed, 1023))
    rightSpeed = max(0, min(rightSpeed, 1023))
    ENA.duty(leftSpeed)
    ENB.duty(rightSpeed)

def forWard(speed=512):
    in1.value(0)
    in2.value(1)
    in3.value(0)
    in4.value(1)
    setSpeed(speed, speed)

def goBack(speed=512):
    in1.value(1)
    in2.value(0)
    in3.value(1)
    in4.value(0)
    setSpeed(speed, speed)

def turnLeft(speed=512):
    in1.value(0)
    in2.value(0)
    in3.value(0)
    in4.value(1)
    setSpeed(0, speed)

def turnRight(speed=512):
    in1.value(0)
    in2.value(1)
    in3.value(0)
    in4.value(0)
    setSpeed(speed, 0)

def servoCam(goc):
    servoX.duty(goc)
    time.sleep(1)
    servoY.duty(30)
    time.sleep(3)
    servoY.duty(120)
    time.sleep(3)
    servoX.duty(77)
    servoY.duty(77)

def distanceFound():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    while echo.value() == 0:
        pass
    start = time.ticks_us()

    while echo.value() == 1:
        pass
    end = time.ticks_us()

    duration = time.ticks_diff(end, start)
    distanceF = int((duration / 2) / 29.412)
    return distanceF

def calculate_distance(left, right):
    avg_pulse = (left + right)
    distance = (avg_pulse / ppr) * wheelC
    return distance * 10

def main():
    servo.duty(77)
    time.sleep(0.5)

    while True:
        khoangcach = distanceFound()
        print("Khoảng cách:", khoangcach, "cm")

        distance = calculate_distance(pulse_countL, pulse_countR)

        if khoangcach > limited or khoangcach == 0:
            khoangcach = distanceFound()
            if khoangcach > limited or khoangcach == 0:
                forWard()
        else:
            resetdongco()
            print("Pulses:", pulse_countL, pulse_countR, "Distance:", distance)
            servoCam(77)
            time.sleep(2)
            send_data_to_server(distance)
            servo.duty(120)
            time.sleep(1)
            khoangcachtrai = distanceFound()
            servo.duty(30)
            time.sleep(1)
            khoangcachphai = distanceFound()
            servo.duty(77)

            if khoangcachphai < 10 and khoangcachtrai < 10:
                resetdongco()
                time.sleep(1)
                send_data_to_server(distance)
                time.sleep(1)
                servoCam(120)
                time.sleep(2)
                servoCam(30)
                time.sleep(2)
                goBack()
            else:
                if khoangcachphai > khoangcachtrai:
                    resetdongco()
                    time.sleep(1)
                    send_data_to_server(distance)
                    time.sleep(1)
                    servoCam(120)
                    time.sleep(2)
                    goBack()
                    time.sleep(1)
                    resetdongco()
                    time.sleep(1)
                    turnLeft()
                    time.sleep(1)
                elif khoangcachphai < khoangcachtrai:
                    resetdongco()
                    time.sleep(1)
                    send_data_to_server(distance)
                    time.sleep(1)
                    servoCam(30)
                    time.sleep(2)
                    goBack()
                    time.sleep(1)
                    resetdongco()
                    time.sleep(1)
                    turnRight()
                    time.sleep(1)

if __name__ == "__main__":
    conn_wifi(ssid, wifi_pass)
    main()