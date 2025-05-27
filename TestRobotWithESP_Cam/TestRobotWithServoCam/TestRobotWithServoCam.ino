#include <ESP32Servo.h>

Servo servoSA;
Servo servoX;
Servo servoY;

#define SERVO_X_PIN 33
#define SERVO_Y_PIN 26
#define SERVO_SA_PIN 25

//HCSR_04
#define trigPin 16
#define echoPin 17
//Motor
#define MLa 12
#define MLb 13
#define ENA 14 

#define MRa 2
#define MRb 4
#define ENB 27 
long duration, distance;

void setup() {
  Serial.begin(115200);

  //Set up Motor
  pinMode(MLa, OUTPUT);
  pinMode(MLb, OUTPUT);
  pinMode(MRa, OUTPUT);
  pinMode(MRb, OUTPUT);

  ledcSetup(0, 1000, 8); //chanel 0, 1000hz, phan giai 8bit
  ledcAttachPin(ENA, 0); //gan chan GPIO 14 vao kenh 0 de dieu khien

  ledcSetup(1, 1000, 8); //chanel 1, 1000hz, do phan giai 8bit
  ledcAttachPin(ENB, 1); //gan chan 27 vao kenh 1

  //Set up HCSR_04
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  //Attach servo
  servoSA.attach(SERVO_SA_PIN);
  servoX.attach(SERVO_X_PIN);
  servoY.attach(SERVO_Y_PIN);
  //Set up servo
  servoSA.write(90);
  servoX.write(90);
  servoY.write(90);
}

void setSpeed(int leftSpeed, int rightSpeed)
{
  leftSpeed = constrain(leftSpeed, 0, 255); //gioi han toc do 225
  rightSpeed = constrain(rightSpeed, 0, 255);

  ledcWrite(0, leftSpeed); // gan chan leftSpeed vao kenh 0 chung voi chan 14
  ledcWrite(1, rightSpeed);
}

void forward(int speed = 200) {
  digitalWrite(MLa, LOW);
  digitalWrite(MLb, HIGH);
  digitalWrite(MRa, LOW);
  digitalWrite(MRb, HIGH);
  setSpeed(speed, speed);
}

void backward(int speed = 200) {
  digitalWrite(MLa, HIGH);
  digitalWrite(MLb, LOW);
  digitalWrite(MRa, HIGH);
  digitalWrite(MRb, LOW);
  setSpeed(speed, speed);
}

void turnLeft(int speed = 200) {
  digitalWrite(MLa, LOW);
  digitalWrite(MLb, LOW);
  digitalWrite(MRa, LOW);
  digitalWrite(MRb, HIGH);
  setSpeed(0, speed);
}

void turnRight(int speed = 200) {
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

void captureObstacle(int panAngle) {
  servoX.write(panAngle);
  servoY.write(20);
  delay(500);

  servoY.write(160);
  delay(500);
  
  servoX.write(90);
  servoY.write(90);
}

void resetServo(){
  servoSA.write(90);
  servoX.write(90);
  servoY.write(90);
}

void MeasureDistance()
{
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  duration = pulseIn(echoPin, HIGH);
  distance = duration / 58.2;
  Serial.print("Distance: ");
  Serial.println(distance);
}

bool checkDirection(int angle)
{
  servoSA.write(angle);
  delay(300);
  MeasureDistance();
  return (distance > 30);
}

void scanCapture() {
  stopMotors();
  
  servoSA.write(0);
  delay(500);
  MeasureDistance();
  if(distance <= 30) {
    captureObstacle(0);
    backward(130);
    delay(300);
    turnRight(130);
    delay(300);
    return;
  }

  servoSA.write(90);
  delay(500);
  MeasureDistance();
  if(distance <= 30) {
    captureObstacle(90);
    backward(130);
    delay(300);
    
    bool leftClear = checkDirection(0);
    bool rightClear = checkDirection(180);
    
    if(leftClear && rightClear) {
      turnLeft(130);
    } 
    else if(leftClear) {
      turnLeft(130);
    }
    else if(rightClear) {
      turnRight(130);
    }
    else {
      backward(130);
      delay(500);
    }
    resetServo();
    return;
  }

  servoSA.write(180);
  delay(500);
  MeasureDistance();
  if(distance <= 30) {
    captureObstacle(180);
    backward(130);
    delay(300);
    turnLeft(130);
    delay(300);
  }
  resetServo();
}

void loop() {
  resetServo();
  MeasureDistance();

  if (distance > 30) {
    servoSA.write(90);
    forward(130);                                                 
  }
  else if (distance <= 30 && distance > 0) {
    scanCapture();
  }
  delay(100);
}