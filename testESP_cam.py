from machine import Pin
import time

# Cấu hình
TRIGGER_OUT_PIN = 4
FLASH_LED_PIN = 2
CAPTURE_INTERVAL = 10

trigger_pin = Pin(TRIGGER_OUT_PIN, Pin.OUT)
trigger_pin.value(1)     # Mặc định ở mức HIGH

# Khởi tạo chân điều khiển đèn Flash LED
flash_led = Pin(FLASH_LED_PIN, Pin.OUT)
flash_led.value(0)       # Mặc định tắt

# Khởi tạo đèn LED cho phản hồi trực quan
status_led = Pin(2, Pin.OUT)  # Đèn LED tích hợp trên nhiều board ESP32

def control_flash(state):
    """Điều khiển đèn Flash LED"""
    flash_led.value(1 if state else 0)
    
def send_trigger():
    """Gửi xung LOW để kích hoạt ESP32-CAM chụp ảnh"""
    print("Gửi tín hiệu chụp ảnh...")
    
    # Bật LED trạng thái
    status_led.value(1)
    
    # Bật đèn Flash trước khi chụp
    control_flash(True)
    time.sleep(0.5)  # Chờ đèn Flash ổn định
    
    # Gửi xung LOW kích hoạt
    trigger_pin.value(0)
    time.sleep(0.1)  # Giữ xung LOW trong 100ms
    trigger_pin.value(1)  # Trở về HIGH
    
    # Chờ một chút để ESP32-CAM bắt đầu quá trình chụp
    time.sleep(0.5)
    
    # Giữ đèn Flash sáng thêm một lúc để ESP32-CAM chụp ảnh
    time.sleep(1)
    
    # Tắt đèn Flash
    control_flash(False)
    
    # Tắt LED trạng thái
    status_led.value(0)
    
    print("Đã gửi tín hiệu xong!")

# Vòng lặp chính
print("=== Chương trình gửi tín hiệu chụp ảnh ===")

# Nhấp nháy LED trạng thái lúc khởi động để biết chương trình đã chạy
for _ in range(3):
    status_led.value(1)
    time.sleep(0.1)
    status_led.value(0)
    time.sleep(0.1)

try:
    count = 0
    while True:
        count += 1
        print(f"Lần chụp thứ {count}")
        
        # Gửi tín hiệu chụp
        send_trigger()
        
        # Chờ đến lần chụp tiếp theo
        print(f"Chờ {CAPTURE_INTERVAL} giây...")
        time.sleep(CAPTURE_INTERVAL)
        
except KeyboardInterrupt:
    print("Chương trình đã dừng")
    # Đảm bảo tắt đèn Flash khi thoát
    control_flash(False)