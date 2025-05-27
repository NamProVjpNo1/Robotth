#define MLa 12
#define MLb 13
#define ENA 14 

#define MRa 2
#define MRb 4
#define ENB 27 

void setup() {
  pinMode(MLa, OUTPUT);
  pinMode(MLb, OUTPUT);
  pinMode(MRa, OUTPUT);
  pinMode(MRb, OUTPUT);
  ledcSetup(0, 1000, 8); //chanel 0, 1000hz, phan giai 8bit
  ledcAttachPin(ENA, 0); //gan chan GPIO 14 vao kenh 0 de dieu khien

  ledcSetup(1, 1000, 8); //chanel 1, 1000hz, do phan giai 8bit
  ledcAttachPin(ENB, 1); //gan chan 27 vao kenh 1
  Serial.begin(115200);
}

void setSpeed(int leftSpeed, int rightSpeed)
{
  leftSpeed = constrain(leftSpeed, 0, 255); //gioi han toc do 225
  rightSpeed = constrain(rightSpeed, 0, 255);

  ledcWrite(0, leftSpeed); // gan chan leftSpeed vao kenh 0 chung voi chan 14
  ledcWrite(1, rightSpeed);
}

void logAction(const char* action) {
  Serial.print(millis());
  Serial.print(" ms -> ");
  Serial.println(action);
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

void loop() {

  logAction("forward");
  forward(130);
  delay(1000);

  logAction("Dừng");
  stopMotors();
  delay(1000);

  logAction("Bắt đầu lùi");
  backward(130);
  delay(1000);
  logAction("Kết thúc lùi");

  logAction("Dừng");
  stopMotors();
  delay(1000);

  logAction("Bắt đầu quay trái");
  turnLeft(130);
  delay(1000);
  logAction("Kết thúc quay trái");

  logAction("Bắt đầu quay phải");
  turnRight(130);
  delay(1000);
  logAction("Kết thúc quay phải");

  logAction("Dừng");
  stopMotors();
  delay(1000);
}