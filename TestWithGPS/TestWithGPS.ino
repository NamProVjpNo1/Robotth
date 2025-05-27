#include <ESP32Servo.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <WiFi.h>
#include <HTTPClient.h>

//Wifi conn and database
const char* ssid = "Banh Mi";
const char* password = "banhbao2022";
const char* serverUrl = "https://192.168.1.2/php/ESP32CAM/photo.php";

Servo servoSA;
Servo servoX;
Servo servoY;

#define SERVO_X_PIN 21
#define SERVO_Y_PIN 19
#define SERVO_SA_PIN 18

//ESP32 CAM
#define CAM_TRIGGER_PIN 25

//HCSR_04
#define trigPin 15
#define echoPin 5

//Motor
#define MLa 2
#define MLb 13
#define MRa 4
#define MRb 12

//Neo6m V2
#define tx_pin 16
#define rx_pin 17
SoftwareSerial gpsSerialPort(rx_pin, tx_pin);
TinyGPSPlus gps;

float latitude = 0;
float longitude = 0;

long duration, distance;

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(9600);
  //Connect to Wifi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
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

void readGPS() {
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      if (gps.location.isValid()) {
        latitude = gps.location.lat();
        longitude = gps.location.lng();
      }
    }
  }
}

void sendToMySQL(float lat, float lng) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    String url = String(serverUrl) + "?lat=" + String(lat, 6) + "&lng=" + String(lng, 6);
    
    http.begin(url);
    int httpCode = http.GET();
    
    if (httpCode > 0) {
      Serial.printf("GPS data sent: %.6f, %.6f\n", lat, lng);
    } else {
      Serial.println("Error sending data");
    }
    http.end();
  } else {
    Serial.println("WiFi disconnected");
  }
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

  readGPS();

  servoX.write(panAngle);
  servoY.write(20);
  delay(500);
  
  triggerCam();
  delay(200);

  servoY.write(160);
  delay(500);

  triggerCam();
  delay(200);

  if (latitude != 0 && longitude != 0) {
    sendToMySQL(latitude, longitude);
  }
  else 
  {
    Serial.println("No valid GPS data");
  }
  
  servoX.write(90);
  servoY.write(90);
}

void measureDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH);
  distance = duration / 58.2;
  
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
}

void scanCapture() {
  stopMotors();

  int scanAngles[] = {0, 90, 180};
  bool obstacleFound = false;

  for(int i = 0; i < 3; i++) {
    servoSA.write(scanAngles[i]);
    delay(800);
    
    measureDistance();
    Serial.print("Scan at ");
    Serial.print(scanAngles[i]);
    Serial.print("° - Distance: ");
    Serial.println(distance);

    if(distance <= 15 && distance > 0) {
      obstacleFound = true;
      Serial.print("Obstacle detected at ");
      Serial.print(scanAngles[i]);
      Serial.println("°");
      
      captureObstacle(scanAngles[i]);
      
      avoidObstacle(scanAngles[i]);
      break;
    }
  }

  if(!obstacleFound) {
    Serial.println("No obstacle detected");
    servoSA.write(90);
  }
}

void avoidObstacle(int obstacleDir) {
  moveBackward();
  delay(500);
  stopMotors();

  if(obstacleDir == 0) {
    turnRight();
  } 
  else if(obstacleDir == 180) {
    turnLeft();
  } 
  else {
    servoSA.write(0);
    delay(500);
    measureDistance();
    long leftDist = distance;
    
    servoSA.write(180);
    delay(500);
    measureDistance();
    long rightDist = distance;
    
    if(leftDist > rightDist && leftDist > 20) {
      turnLeft();
    } else if(rightDist > 20) {
      turnRight();
    } else {
      moveBackward();
      delay(1000);
    }
  }
  delay(500);
  stopMotors();
}

void loop() {
  measureDistance();

  if (distance > 15) {
    servoSA.write(90);
    moveForward();                                                     
  }
  else if (distance <= 15 && distance > 0) {
    scanCapture();
  }
  
  delay(100);
}
