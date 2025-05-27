// ULTRASONIC OBSTACLE AVOIDING CAR BASED ON ARDUINO //

// Before uploading the code you have to install the following necessary library //

// 1. Adafruit Motor Shield library (Note: Do not install the Adafruit Motor Shield V2 Library)
// 2. NewPing Library

// To Install the libraries go to Tools >> Manage Libraries >> Search Library by its name >> Select the install the library //


#include <AFMotor.h>
#include <NewPing.h>
#include <Servo.h>

#define TRIG_PIN A1
#define ECHO_PIN A0
#define MAX_DISTANCE 200
#define MAX_SPEED 255


NewPing radar(TRIG_PIN, ECHO_PIN, MAX_DISTANCE);

AF_DCMotor motor1(1);
AF_DCMotor motor2(2);
AF_DCMotor motor3(3);
AF_DCMotor motor4(4);
Servo myservo;


int distance = 100;
int pos = 0;


void setup() {
  motor1.setSpeed(200);
  motor2.setSpeed(200);
  motor3.setSpeed(200);
  motor4.setSpeed(200);

  myservo.attach(9);
  myservo.write(100);
  delay(2000);
  distance = checkDistance();
  delay(100);
  distance = checkDistance();
  delay(100);
  distance = checkDistance();
  delay(100);
  distance = checkDistance();
  delay(100);
  Serial.begin(9600);
}

void loop() {
  int distanceRight = 0;
  int distanceLeft = 0;
  delay(40);

  if (distance <= 15) {
    stopMovement();
    delay(100);
    moveBackward();
    delay(300);
    stopMovement();
    delay(200);
    distanceRight = checkRightDistance();
    delay(200);
    distanceLeft = checkLeftDistance();
    delay(200);

    if (distanceRight >= distanceLeft) {
      turnRight();
      stopMovement();
    } else {
      turnLeft();
      stopMovement();
    }
  } else {
    moveForward();
  }
  distance = checkDistance();
  Serial.println(distance);
}

int checkRightDistance() {
  for (pos = 100; pos >= 30; pos -= 1) {
    myservo.write(pos);
    delay(5);
  }
  myservo.write(30);
  delay(500);
  int distance = checkDistance();
  delay(100);
  for (pos = 30; pos <= 100; pos += 1) {
    myservo.write(pos);
    delay(5);
  }
  myservo.write(100);
  return distance;
}

int checkLeftDistance() {
  for (pos = 100; pos <= 170; pos += 1) {
    myservo.write(pos);
    delay(5);
  }
  myservo.write(170);
  delay(500);
  int distance = checkDistance();
  delay(100);
  for (pos = 170; pos >= 100; pos -= 1) {
    myservo.write(pos);
    delay(5);
  }
  myservo.write(100);
  return distance;
  delay(100);
}

int checkDistance() {
  delay(70);
  int cm = radar.ping_cm();
  if (cm == 0) {
    cm = 250;
  }
  return cm;
}

void stopMovement() {
  motor1.run(RELEASE);
  motor2.run(RELEASE);
  motor3.run(RELEASE);
  motor4.run(RELEASE);
}

void moveForward() {
  motor1.run(FORWARD);
  motor2.run(FORWARD);
  motor3.run(FORWARD);
  motor4.run(FORWARD);
}

void moveBackward() {
  motor1.run(BACKWARD);
  motor2.run(BACKWARD);
  motor3.run(BACKWARD);
  motor4.run(BACKWARD);
}

void turnLeft() {
  motor1.run(FORWARD);
  motor2.run(FORWARD);
  motor3.run(BACKWARD);
  motor4.run(BACKWARD);
  delay(500);
  motor1.run(FORWARD);
  motor2.run(FORWARD);
  motor3.run(FORWARD);
  motor4.run(FORWARD);
}

void turnRight() {
  motor1.run(BACKWARD);
  motor2.run(BACKWARD);
  motor3.run(FORWARD);
  motor4.run(FORWARD);
  delay(500);
  motor1.run(FORWARD);
  motor2.run(FORWARD);
  motor3.run(FORWARD);
  motor4.run(FORWARD);
}