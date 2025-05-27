#include <dummy.h>
#include <ESP32Servo.h>
Servo Myservo;

#define trigPin 15
#define echoPin 5

// Motor pins
#define MLa 12
#define MLb 13
#define ENA 14 

#define MRa 2
#define MRb 4
#define ENB 27

long duration, distance;


void setSpeed(int leftSpeed, int rightSpeed) {
  leftSpeed = constrain(leftSpeed, 0, 255);
  rightSpeed = constrain(rightSpeed, 0, 255);
  ledcWrite(0, leftSpeed);   // ENA (kênh 0)
  ledcWrite(1, rightSpeed);  // ENB (kênh 1)
}

void setup() {
  Serial.begin(115200);

  // Motor setup
  pinMode(MLa, OUTPUT);
  pinMode(MLb, OUTPUT);
  pinMode(MRa, OUTPUT);
  pinMode(MRb, OUTPUT);

  // PWM setup
  ledcSetup(0, 1000, 8);      // channel 0 for ENA
  ledcAttachPin(ENA, 0);
  ledcSetup(1, 1000, 8);      // channel 1 for ENB
  ledcAttachPin(ENB, 1);

  // Cảm biến siêu âm
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  Myservo.attach(26);  // Gắn servo vào GPIO14
}

void forward(int speed = 500) {
  digitalWrite(MLa, LOW);
  digitalWrite(MLb, HIGH);
  digitalWrite(MRa, LOW);
  digitalWrite(MRb, HIGH);
  setSpeed(speed, speed);
}

void backward(int speed = 500) {
  digitalWrite(MLa, HIGH);
  digitalWrite(MLb, LOW);
  digitalWrite(MRa, HIGH);
  digitalWrite(MRb, LOW);
  setSpeed(speed, speed);
}

void turnLeft(int speed = 500) {
  digitalWrite(MLa, LOW);
  digitalWrite(MLb, LOW);
  digitalWrite(MRa, LOW);
  digitalWrite(MRb, HIGH);
  setSpeed(0, speed);
}

void turnRight(int speed = 500) {
  digitalWrite(MLa, LOW);
  digitalWrite(MLb, HIGH);
  digitalWrite(MRa, LOW);
  digitalWrite(MRb, LOW);
  setSpeed(speed, 0);
}

void stopMotors() {
  digitalWrite(MLa, LOW);
  digitalWrite(MLb, LOW);
  digitalWrite(MRa, LOW);
  digitalWrite(MRb, LOW);
  setSpeed(0, 0);
}

void loop() {
  // Đo khoảng cách
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);   
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  duration = pulseIn(echoPin, HIGH, 25000);
  distance = duration / 58.2;

  Serial.println(distance);
  delay(10);

  if (distance > 20) {
    Myservo.write(90);
    forward();
  } 
  else if ((distance < 15) && (distance > 0)) {
    stopMotors();
    delay(100);

    Myservo.write(0);
    delay(500);
    Myservo.write(180);
    delay(500);
    Myservo.write(90);
    delay(500);

    backward();
    delay(500);

    stopMotors();
    delay(100);

    turnLeft();
    delay(500);
  }
}
