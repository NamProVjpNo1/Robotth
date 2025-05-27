from machine import Pin, PWM
import time

# Khai báo chân GPIO cho cảm biến HC-SR04
trig = Pin(15, Pin.OUT)
echo = Pin(5, Pin.IN)

# Khai báo chân GPIO cho servo
servo = PWM(Pin(19), freq=50)  # Tần số 50 Hz cho servo

# Hàm đo khoảng cách sử dụng HC-SR04
def dokhoangcach():
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
    
    # Tính khoảng cách (cm)
    duration = time.ticks_diff(end, start)
    distance = int((duration / 2) / 29.412)
    return distance

# Hàm điều khiển servo quay đến góc 180 độ (quay sang trái)
def quay_sang_trai():
    servo.duty(125)  # Góc 180 độ
    time.sleep(1)

# Hàm điều khiển servo quay về giữa (90 độ)
def quay_ve_giua():
    servo.duty(77)  # Góc 90 độ
    time.sleep(1)

# Hàm điều khiển servo quay đến góc 0 độ (quay sang phải)
def quay_sang_phai():
    servo.duty(25)  # Góc 0 độ
    time.sleep(1)

# Chương trình chính
def main():
    servo.duty(77)  # Khởi tạo servo ở góc 90 độ
    time.sleep(0.5)

    while True:
        khoangcach = dokhoangcach()  # Đo khoảng cách

        print("Khoảng cách: {} cm".format(khoangcach))  # Hiển thị khoảng cách đo được

        # Dựa trên khoảng cách đo được, điều khiển servo
        if khoangcach < 10:  # Nếu khoảng cách nhỏ hơn 10 cm
            quay_sang_trai()  # Quay sang trái (180 độ)
        elif khoangcach > 20:  # Nếu khoảng cách lớn hơn 20 cm
            quay_sang_phai()  # Quay sang phải (0 độ)
        else:  # Khoảng cách từ 10 cm đến 20 cm
            quay_ve_giua()  # Quay về giữa (90 độ)

# Chạy chương trình
if __name__ == "__main__":
    main()
