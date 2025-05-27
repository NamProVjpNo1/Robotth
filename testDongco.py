from machine import Pin, PWM
import time

# Dong co
in1 = Pin(12, Pin.OUT)
in2 = Pin(14, Pin.OUT)
in3 = Pin(27, Pin.OUT)
in4 = Pin(26, Pin.OUT)

ENA = PWM(Pin(13), freq=1000, duty=0)
ENB = PWM(Pin(25), freq=1000, duty=0)

def setSpeed(leftSpeed, rightSpeed):
    leftSpeed = max(0, min(leftSpeed, 1023))
    rightSpeed = max(0, min(rightSpeed, 1023))
    ENA.duty(leftSpeed)
    ENB.duty(rightSpeed)

def resetMotor():
    in1.value(0)
    in2.value(0)
    in3.value(0)
    in4.value(0)
    setSpeed(0, 0)

def forWard(speed=512):
    in1.value(1)
    in2.value(0)
    in3.value(1)
    in4.value(0)
    setSpeed(speed, speed)

def backWard(speed=512):
    in1.value(0)
    in2.value(1)
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
    in1.value(1)
    in2.value(0)
    in3.value(0)
    in4.value(0)
    setSpeed(speed, 0)
    
def main():
    while True:
        forWard()
        time.sleep(3)
        resetMotor()
        time.sleep(1)
        backWard()
        time.sleep(3)
        resetMotor()
        time.sleep(1)
        turnLeft()
        time.sleep(3)
        resetMotor()
        time.sleep(1)
        turnRight()
        time.sleep(3)
        resetMotor()

if __name__ == "__main__":
    main()

