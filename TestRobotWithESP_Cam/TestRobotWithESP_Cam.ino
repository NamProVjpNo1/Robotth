#include <ESP32Servo.h>

Servo servoSA;
Servo servoX;
Servo servoY;

#define SERVO_X_PIN 13
#define SERVO_Y_PIN 14
#define SERVO_SA_PIN 12

//ESP32 CAM
#define CAM_TRIGGER_PIN 12

//HCSR_04
#define trigPin 9
#define echoPin 8
//Motor
#define MLa 4
#define MLb 5
#define MRa 6
#define MRb 7
long duration, distance;

void setup() {
  Serial.begin(9600);
  //Set up ESP32 CAM
  pinMode(CAM_TRIGGER_PIN, OUTPUT);
  digitalWrite(CAM_TRIGGER_PIN, LOW);

  //Set up Motor
  pinMode(MLa, OUTPUT);
  pinMode(MLb, OUTPUT);
  pinMode(MRa, OUTPUT);
  pinMode(MRb, OUTPUT);
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

void moveForward() {
  digitalWrite(MRb, HIGH);
  digitalWrite(MRa, LOW);
  digitalWrite(MLb, HIGH);
  digitalWrite(MLa, LOW);
}

void moveBackward() {
  digitalWrite(MRb, LOW);
  digitalWrite(MRa, HIGH);
  digitalWrite(MLb, LOW);
  digitalWrite(MLa, HIGH);
}

void turnLeft() {
  digitalWrite(MRb, HIGH);
  digitalWrite(MRa, LOW);
  digitalWrite(MLb, LOW);
  digitalWrite(MLa, HIGH);
}

void turnRight() {
  digitalWrite(MRb, LOW);
  digitalWrite(MRa, HIGH);
  digitalWrite(MLb, HIGH);
  digitalWrite(MLa, LOW);
}

void stopMotors() {
  digitalWrite(MRb, LOW);
  digitalWrite(MRa, LOW);
  digitalWrite(MLb, LOW);
  digitalWrite(MLa, LOW);
}

void triggerCam() {
  digitalWrite(CAM_TRIGGER_PIN, HIGH);
  delayMicroseconds(100);
  digitalWrite(CAM_TRIGGER_PIN, LOW);
}

void captureObstacle(int panAngle) {
  servoX.write(panAngle);
  servoY.write(20);
  delay(500);
  
  triggerCam();
  delay(200);

  servoY.write(160);
  delay(500);

  triggerCam();
  delay(200);
  
  servoX.write(90);
  servoY.write(90);
}

void MeasureDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  duration = pulseIn(echoPin, HIGH);
  distance = duration / 58.2;
  Serial.print("Distance: ");
  Serial.println(distance);
}

void scanCapture() {
  stopMotors();

  servoSA.write(0);
  delay(1000);
  MeasureDistance();
  if(distance <= 15) {
    captureObstacle(0);
    delay(500);
    moveBackward();
    delay(500);
    stopMotors();
    delay(100);
    turnRight();
    delay(500);
    return;
  }

  servoSA.write(90);
  delay(1000);
  MeasureDistance();
  if(distance <= 15) {
    captureObstacle(90);
    delay(500);
    moveBackward();
    delay(500);
    stopMotors();
    delay(500);
    
    servoSA.write(0);
    delay(500);
    MeasureDistance();
    if(distance > 15) {
      turnLeft();
      delay(500);
    } 
    else {
      servoSA.write(180);
      delay(500);
      MeasureDistance();
      if(distance > 15) {
        turnRight();
        delay(500);
      }
      else {
        moveBackward();
        delay(500);
      }
    }
    return;
  }

  servoSA.write(180);
  delay(1000);
  MeasureDistance();
  if(distance <= 15) {
    captureObstacle(180);
    delay(500);
    moveBackward();
    delay(500);
    turnLeft();
    delay(500);
  }
  
  servoSA.write(90);
}

void loop() {
  MeasureDistance();

  if (distance > 15) {
    servoSA.write(90);
    moveForward();                                                     
  }
  else if (distance <= 15 && distance > 0) {
    scanCapture();
  }
  
  delay(100);
}