from machine import Pin, UART, PWM
import urequests
import json
import time
import network
import math

# WiFi config
ssid = 'Banh Mi'
wifi_pass = 'banhbao2022'

#robot_id
robot_id = "RB1234"

# Ultrasonic sensor
trig = Pin(2, Pin.OUT)
echo = Pin(4, Pin.IN)
limited = 25

# Camera UART và trigger
uart_cam = UART(1, baudrate=115200, rx=32, tx=33)
cam_trigger = Pin(21, Pin.OUT)

# UART cho GPS
uart_gps = UART(2, baudrate=9600, tx=17, rx=16)

# Encoder
pulse_countL = 0
pulse_countR = 0
ppr = 20
wheel_dmt = 0.065
wheelC = math.pi * wheel_dmt

def countPulseL(pin):
    global pulse_countL
    pulse_countL += 1

def countPulseR(pin):
    global pulse_countR
    pulse_countR += 1

lPinP = Pin(34, Pin.IN)
rPinP = Pin(35, Pin.IN)
lPinP.irq(trigger=Pin.IRQ_RISING, handler=countPulseL)
rPinP.irq(trigger=Pin.IRQ_RISING, handler=countPulseR)

# Động cơ
in1 = Pin(12, Pin.OUT)
in2 = Pin(14, Pin.OUT)
in3 = Pin(27, Pin.OUT)
in4 = Pin(26, Pin.OUT)
ENA = PWM(Pin(13), freq=1000, duty=0)
ENB = PWM(Pin(25), freq=1000, duty=0)

# Servo
servo = PWM(Pin(15), freq=50)
servoX = PWM(Pin(18), freq=50)
servoY = PWM(Pin(19), freq=50)

latitude = 0.0
longitude = 0.0

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

def send_sensor_uart(distance, robot_id):
    read_gps()
    msg = f"{longitude},{latitude},{distance}, {robot_id}\n"
    uart_cam.write(msg)
    print("Đã gửi dữ liệu qua UART:", msg.strip())
    time.sleep(0.1)

def triggerCam():
    print("Gửi tín hiệu trigger tới ESP32-CAM...")
    cam_trigger.value(1)
    time.sleep(1)
    cam_trigger.value(0)
    time.sleep(0.5)
    cam_trigger.value(1)
    print("Đã gửi xong tín hiệu trigger\n")
    time.sleep(3) 

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

def forWard(speed=550):
    in1.value(1)
    in2.value(0)
    in3.value(0)
    in4.value(1)
    setSpeed(speed, speed)

def goBack(speed=550):
    in1.value(0)
    in2.value(1)
    in3.value(1)
    in4.value(0)
    setSpeed(speed, speed)

def turnLeft(speed=550):
    in1.value(0)
    in2.value(1)
    in3.value(0)
    in4.value(0)
    setSpeed(speed, 0)

def turnRight(speed=550):
    in1.value(0)
    in2.value(0)
    in3.value(1)
    in4.value(0)
    setSpeed(0, speed)


def distanceFound():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    timeout = time.ticks_us() + 30000  # 30ms timeout
    
    while echo.value() == 0:
        if time.ticks_us() > timeout:
            print("HCSR04 timeout - echo không lên HIGH")
            return 0
    start = time.ticks_us()

    timeout = time.ticks_us() + 30000
    while echo.value() == 1:
        if time.ticks_us() > timeout:
            print("HCSR04 timeout - echo không xuống LOW")
            return 0
    end = time.ticks_us()

    duration = time.ticks_diff(end, start)
    distanceF = int((duration / 2) / 29.412)
    
    if distanceF < 2 or distanceF > 400:
        print(f"HCSR04 giá trị không hợp lệ: {distanceF}cm")
        return 0
    
    return distanceF

def servoCam(goc):
    servoX.duty(goc)
    time.sleep(1)
    
    servoY.duty(60)
    time.sleep(1)
    triggerCam()
    
    servoY.duty(100)
    time.sleep(1)
    triggerCam()

    servoX.duty(77)
    servoY.duty(77)
    time.sleep(1)
    
def calculate_distance(left, right):
    avg_pulse = (left + right) / 2
    distance = (avg_pulse / ppr) * wheelC
    return distance * 10

def safe_distance_read(retries=3):
    for i in range(retries):
        distance = distanceFound()
        if distance > 0:
            return distance
        print(f"Retry đọc HCSR04 lần {i+1}")
        time.sleep(0.05)
    return 0

def main():
    servo.duty(77)
    servoX.duty(77)
    servoY.duty(77)
    time.sleep(0.5)
    
    while True:
        khoangcach = safe_distance_read()
        print("Khoảng cách:", khoangcach, "cm")

        distance = calculate_distance(pulse_countL, pulse_countR)

        if khoangcach > limited or khoangcach == 0:
            khoangcach = safe_distance_read()
            if khoangcach > limited or khoangcach == 0:
                forWard()
                time.sleep(0.1)
        else:
            resetdongco()
            print("Pulses:", pulse_countL, pulse_countR, "Distance:", distance)
            
            send_sensor_uart(distance, robot_id)
            
            servoCam(77)
            
            servo.duty(120)
            time.sleep(0.3)
            khoangcachtrai = safe_distance_read()
            print("Khoảng cách trái:", khoangcachtrai, "cm")
            time.sleep(3)
            
            servo.duty(30)
            time.sleep(0.3)
            khoangcachphai = safe_distance_read()
            print("Khoảng cách phải:", khoangcachphai, "cm")
            time.sleep(3)
            
            servo.duty(77)
            time.sleep(0.2)

            if khoangcachphai < 10 and khoangcachtrai < 10:
                resetdongco()
                
                send_sensor_uart(distance, robot_id)
                servoCam(110)
                time.sleep(0.2)
                servoCam(50)
                
                goBack()
                time.sleep(0.8)
                resetdongco()
            else:
                if khoangcachphai > khoangcachtrai:
                    resetdongco()
                    
                    send_sensor_uart(distance, robot_id)
                    servoCam(110)
                    
                    goBack()
                    time.sleep(0.5)
                    resetdongco()
                    time.sleep(0.2)
                    turnLeft()
                    time.sleep(0.8)
                    resetdongco()
                    
                elif khoangcachphai < khoangcachtrai:
                    resetdongco()
                    
                    send_sensor_uart(distance, robot_id) 
                    servoCam(50)
                    
                    goBack()
                    time.sleep(0.5)
                    resetdongco()
                    time.sleep(0.2)
                    turnRight()
                    time.sleep(0.8)
                    resetdongco()

        time.sleep(0.05)

if __name__ == "__main__":
    try:
        conn_wifi(ssid, wifi_pass)
        time.sleep(0.1)
        main()
    except KeyboardInterrupt:
        print("Dừng robot...")
        resetdongco()
    except Exception as e:
        print("Lỗi:", e)
        resetdongco()
