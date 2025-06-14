from machine import Pin, UART
import time

trigger = Pin(25, Pin.OUT)
uart = UART(1, baudrate=115200, rx=32, tx=33)

def send_gps_data(longitude, latitude, distance):
    data = f"{longitude},{latitude},{distance}\n"
    uart.write(data)
    print(f"Gửi: {data.strip()}")

def trigger_camera():
    print("Gửi tín hiệu trigger tới ESP32-CAM...")
    
    trigger.value(1)
    time.sleep(0.1)
    
    print("Tạo cạnh xuống (HIGH -> LOW)")
    trigger.value(0)
    time.sleep(0.5)
    
    # Trả về HIGH
    print("Trả về HIGH")
    trigger.value(1)
    time.sleep(0.1)
    
    print("Đã gửi xong tín hiệu trigger\n")

def test_trigger_continuous():
    """Test gửi trigger liên tục"""
    print("Bắt đầu test trigger ESP32-CAM")
    print("Kết nối: GPIO25 (MicroPython) -> GPIO12 (ESP32-CAM)")
    print("=" * 50)
    
    counter = 1
    while True:
        longitude = 106.123456
        latitude = 10.987654
        distance = 5.7
        send_gps_data(longitude, latitude, distance)
        time.sleep(3)
        print(f"Lần trigger thứ {counter}")
        trigger_camera()
        counter += 1
        
        print("Chờ 10 giây...")
        time.sleep(10)

def test_single_trigger():
    print("Test gửi một lần trigger")
    trigger_camera()

if __name__ == "__main__":
    trigger.value(1)
    time.sleep(0.1)
    
    print("Chọn chế độ:")
    print("1. Test liên tục (mỗi 10 giây)")
    print("2. Test một lần")
    test_trigger_continuous()
