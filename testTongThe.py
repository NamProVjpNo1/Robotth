from machine import Pin, PWM, UART
import time
import network
import urequests
import math

# --- Wifi ---
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi_ssid = 'Quan Anh'
wifi_password = '01669799620'
wifi.connect(wifi_ssid, wifi_password)
print("Đang kết nối WiFi...")
while not wifi.isconnected():
    print("No wifi connect")
    time.sleep(1)
print('WiFi connected, IP:', wifi.ifconfig())

# --- HCSR-04 ---
trig = Pin(15, Pin.OUT)
echo = Pin(5, Pin.IN)
gioihan = 25  # ngưỡng giới hạn 25 cm

# --- Cấu hình động cơ ---
int1 = Pin(2, Pin.OUT)
int2 = Pin(13, Pin.OUT)
int3 = Pin(4, Pin.OUT)
int4 = Pin(12, Pin.OUT)

# --- servo ---
servo_sa = PWM(Pin(21), freq=50) # Servo cam
servo_ngang = PWM(Pin(19), freq=50)  # Servo quay ngang
servo_doc = PWM(Pin(18), freq=50)  # Servo quay dọc

# --- ESP32-CAM ---
CAMERA_PIN = 25
camera_trigger = Pin(CAMERA_PIN, Pin.OUT)
camera_trigger.value(1)  # HIGH

# --- Neo6m V2 ---
uart_gps = UART(2, baudrate=9600, tx=17, rx=16)

# --- encoder ---
encoder_left = Pin(14, Pin.IN)
encoder_right = Pin(27, Pin.IN)

# Hàm đếm số xung từ encoder
def count_pulses(pin, timeout=150):
    count = 0
    start = time.ticks_ms()
    last_value = pin.value()
    while time.ticks_diff(time.ticks_ms(), start) < timeout:
        current_value = pin.value()
        if last_value == 0 and current_value == 1:
            count += 1
        last_value = current_value
    return count

def read_encoder_distance():
    pulse_left = count_pulses(encoder_left)
    pulse_right = count_pulses(encoder_right)
    pulses_per_rev = 20  # xung
    dia_cm = 6.5  # duong kinh cm
    
    # chu vi
    cir_cm = math.pi * dia_cm

    distance_left_cm = (pulse_left / pulses_per_rev) * cir_cm
    distance_right_cm = (pulse_right / pulses_per_rev) * cir_cm

    distance_cm = (distance_left_cm + distance_right_cm) / 2

    print(f"Distance: {round(distance_cm, 2)} cm")
    return round(distance_cm, 2)

# ham dieu khien dong co
def resetdongco():
    int1.value(0)
    int2.value(0)
    int3.value(0)
    int4.value(0)

def dithang():
    int1.value(0)
    int2.value(1) #tien len cua banh phai
    int3.value(1) #tien len cua banh trai
    int4.value(0)

def dilui():
    resetdongco()
    int1.value(1) #lui cua banh phai
    int2.value(0)
    int3.value(0)
    int4.value(1) #lui cua banh trai
    

def disangtrainho():
    resetdongco()
    int1.value(1)
    time.sleep(0.2)
    resetdongco()

def disangphainho():
    resetdongco()
    int4.value(1)
    time.sleep(0.2)
    resetdongco()

# Ham do khoang cach
def dokhoangcach():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    timeout = time.ticks_ms() + 1000  # 1 giây timeout
    while echo.value() == 0:
        if time.ticks_ms() > timeout:
            return 0  # Không có tín hiệu echo

    start = time.ticks_us()

    timeout = time.ticks_ms() + 1000
    while echo.value() == 1:
        if time.ticks_ms() > timeout:
            return 0

    end = time.ticks_us()
    # tinh khoang cach bang cm
    duration = time.ticks_diff(end, start)
    distance = int((duration / 2) / 29.412)
    return distance

# --- Điều khiển servo ---
def quay_svsa_trai():
    servo_sa.duty(125)
    khoang_cach = dokhoangcach()
    time.sleep(1)
    servo_sa.duty(75)
    return khoang_cach

def quay_sv_ngang_trai():
    servo_ngang.duty(125)
    trigger_camera()
    time.sleep(4)
    servo_ngang.duty(75)

def quay_sv_doc_duoi():
    servo_doc.duty(125)
    trigger_camera()
    time.sleep(4)
    servo_doc.duty(75)

    
def quay_svsa_phai():
    servo_sa.duty(25)
    khoang_cach = dokhoangcach()
    time.sleep(1)
    servo_sa.duty(75)
    return khoang_cach


def quay_sv_ngang_phai():
    servo_ngang.duty(25)
    trigger_camera()
    time.sleep(4)
    servo_ngang.duty(75)

def quay_sv_doc_tren():
    servo_doc.duty(25)
    trigger_camera()
    time.sleep(4)
    servo_doc.duty(75)

def trigger_camera():
    """Activate ESP32-CAM taking picture"""
    lat, lon = get_gps_coordinates()
    distancecm = read_encoder_distance()
    
    # trigger cam
    camera_trigger.value(0)
    time.sleep_ms(100)
    camera_trigger.value(1)
    
    # send data
    if lat and lon:
        metadata = {
            "latitude": lat,
            "longitude": lon,
            "distance": distancecm,
        }
        send_to_server(metadata)
    time.sleep(3)
    
def connect_wifi(max_retries=5):
    retry_count = 0
    while not wifi.isconnected() and retry_count < max_retries:
        try:
            print(f"Connecting to WiFi... (Attempt {retry_count + 1}/{max_retries})")
            wifi.connect(wifi_ssid, wifi_password)
            time.sleep(5)  # Chờ đủ thời gian kết nối
            
            if wifi.isconnected():
                print('WiFi connected, IP:', wifi.ifconfig())
                return True
                
        except Exception as e:
            print("WiFi error:", e)
        
        retry_count += 1
        time.sleep(2)
    
    print("Failed to connect WiFi")
    return False

def get_gps_coordinates(max_retries=3):
    for _ in range(max_retries):
        try:
            if uart_gps.any():
                data = uart_gps.readline()
                data = str(data, 'utf-8')
                
                if "$GPGGA" in data:
                    parts = data.split(",")
                    if len(parts) > 7 and parts[6] != "0":
                        lat_raw = parts[2]
                        lon_raw = parts[4]
                        
                        if lat_raw and lon_raw:
                            lat = convert_to_degrees(lat_raw)
                            lon = convert_to_degrees(lon_raw)
                            return lat, lon
                            
        except UnicodeError:
            print("GPS data decode error")
        except Exception as e:
            print("GPS error:", e)
        
        time.sleep(1)
    
    return None, None

def send_to_server(metadata, max_retries=3):
    url = 'http://192.168.1.15/php/ESP32CAM/photo.php'
    
    for attempt in range(max_retries):
        response = None
        try:
            if not wifi.isconnected():
                if not connect_wifi():
                    print("Skipping server send: No WiFi")
                    return
                    
            response = urequests.post(url, json=metadata)
            print("Send success:", response.status_code)
            return  # Thoát nếu thành công
            
        except Exception as e:
            print(f"Send failed (attempt {attempt+1}/{max_retries}):", e)
            time.sleep(2)
            
        finally:
            if response:
                response.close()
                
def connect_wifi(max_retries=3):
    retry_count = 0
    while not wifi.isconnected() and retry_count < max_retries:
        try:
            print(f"Connecting to WiFi... (Attempt {retry_count + 1}/{max_retries})")
            wifi.connect(wifi_ssid, wifi_password)
            time.sleep(5)  # Chờ đủ thời gian kết nối
            
            if wifi.isconnected():
                print('WiFi connected, IP:', wifi.ifconfig())
                return True
                
        except Exception as e:
            print("WiFi error:", e)
        
        retry_count += 1
        time.sleep(2)
    
    print("Failed to connect WiFi")
    return False
            
def main():
    servo_ngang.duty(75)
    servo_doc.duty(75)
    servo_sa.duty(75)
    time.sleep(1)
    
    if not connect_wifi():
        print("Starting without WiFi!")
    
    while True:
        
        if not wifi.isconnected():
            print("WiFi disconnected! Reconnecting...")
            connect_wifi()
        
        khoangcach = dokhoangcach()
        
        if khoangcach > gioihan or khoangcach == 0:
            dithang()
        else:
            resetdongco()            
            quay_svsa_trai()
            time.sleep(1)
            khoangcach_trai = dokhoangcach()
            quay_svsa_phai()
            time.sleep(1)
            khoangcach_phai = dokhoangcach()
            
            if khoangcach_phai < 10 and khoangcach_trai < 10:
                dilui()
                time.sleep(1)
            else:
                if khoangcach_phai > khoangcach_trai:
                    quay_sv_ngang_trai()
                    time.sleep(1)
                    quay_sv_doc_duoi()
                    time.sleep(1)
                    trigger_camera()
                    quay_sv_doc_tren()
                    time.sleep(1)
                    trigger_camera()
                    time.sleep(1)
                    disangtrainho()
                    time.sleep(0.5)
                else:
                    quay_sv_ngang_phai()
                    time.sleep(1)
                    quay_sv_doc_duoi()
                    time.sleep(1)
                    trigger_camera()
                    quay_sv_doc_tren()
                    time.sleep(1)
                    trigger_camera()
                    time.sleep(1)
                    disangphainho()
                    time.sleep(0.5)

if __name__ == "__main__":
    main()
