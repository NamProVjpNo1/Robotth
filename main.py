from machine import Pin, UART, SoftI2C, PWM
import urequests
import json
import time
import network
import math

# Wifi
ssid = 'Banh Mi'
wifi_pass = 'banhbao2022'
url_send = "http://192.168.1.7/php/ESP32CAM/distance.php"

# Cam bien sieu am
trig = Pin(2, Pin.OUT)
echo = Pin(4, Pin.IN)
limited = 25

# Cam bien encoder lm393ir
pulse_countL = 0
pulse_countR = 0
ppr = 20
wheel_dmt = 0.065
wheelC = math.pi * wheel_dmt

# GPS Neo6mV2
uart = UART(2, baudrate=9600, tx=17, rx=16)
latitude = ""
longitude = ""

float read_gps():
    global latitude, longitude
    timeout = time.time() + 5
    while time.time() < timeout:
        line = uart.readline()
        if line:
            try:
                line = line.decode('utf-8')
                if line.startswith("$GPGGA"):
                    parts = line.split(",")
                    if len(parts) > 5 and parts[2] and parts[3] and parts[4] and parts[5]:
                        lat = parts[2]
                        lat_dir = parts[3]
                        lon = parts[4]
                        lon_dir = parts[5]
                        latitude = nmeaToDecimal(lat, lat_dir)
                        longitude = nmeaToDecimal(lon, lon_dir)
                        print("Latitude:", latitude, "Longitude:", longitude)
                        break
            except:
                pass

def nmeaToDecimal(raw, direction):
    try:
        raw = float(raw)
        degrees = int(raw) // 100
        minutes = raw - (degrees * 100)
        decimal = degrees + minutes / 60
        if direction in ['S', 'W']:
            decimal = -decimal
        return '{:.6f}'.format(decimal)
    except:
        return None

def countPulseL(pin):
    global pulse_countL
    pulse_countL += 1
    
def countPulseR(pin):
    global pulse_countR
    pulse_countR += 1

lPinP = Pin(33, Pin.IN)
rPinP = Pin(32, Pin.IN)
lPinP.irq(trigger = Pin.IRQ_RISING, handler = countPulseL)
rPinP.irq(trigger = Pin.IRQ_RISING, handler = countPulseR)

# Dong co
in1 = Pin(12, Pin.OUT)
in2 = Pin(14, Pin.OUT)
in3 = Pin(27, Pin.OUT)
in4 = Pin(26, Pin.OUT)

ENA = PWM(Pin(13), freq=1000, duty=0)
ENB = PWM(Pin(25), freq=1000, duty=0)

#Servo
servo = PWM(Pin(15), freq=50, duty=77)
servoX = PWM(Pin(18), freq=50, duty=77)
servoY = PWM(Pin(19), freq=50, duty=77)

def conn_wifi(ssid, wifi_pass):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to wifi......")
        wlan.connect(ssid, wifi_pass)
        while not wlan.isconnected():
            time.sleep(0.5)
    print("Wifi: " + str(wlan.ifconfig()) + " is connected")

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
    avg_pulse = (left + right) #chua co encoder phai
    distance = (avg_pulse / ppr) * wheelC
    return distance * 10

def setSpeed(leftSpeed, rightSpeed):
    leftSpeed = max(0, min(leftSpeed, 1023))
    rightSpeed = max(0, min(rightSpeed, 1023))
    ENA.duty(leftSpeed)
    ENB.duty(rightSpeed)

def send_data(distance):
    read_gps()
    try:
        data = {
            "latitude": latitude,
            "longitude": longitude,
            "distance": distance
        }
        response = urequests.post(url_send, json=data)
        print("Sended", response.text)
        response.close()
    except Exception as e:
        print("Error sending data!", e)

def resetdongco():
    in1.value(0)
    in2.value(0)
    in3.value(0)
    in4.value(0)
    setSpeed(0, 0)

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

def main():
    servo.duty(77)
    time.sleep(0.5)

    distance = calculate_distance(pulse_countL, pulse_countR)

    while True:
        khoangcach = distanceFound()
        print("Khoảng cách:", khoangcach, "cm")

        if khoangcach > limited or khoangcach == 0:
            khoangcach = distanceFound()
            if khoangcach > limited or khoangcach == 0:
                forWard()
        else:
            resetdongco()
            distance = calculate_distance(pulse_countL, pulse_countR)
            print("Pulses:", pulse_countL, pulse_countR, "Distance:", distance)

            servoCam(77)
            time.sleep(2)

            send_data(distance)

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
                send_data(distance)
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
                    send_data(distance)
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
                    send_data(distance)
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
