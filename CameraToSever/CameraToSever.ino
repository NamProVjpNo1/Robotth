#include <WiFi.h>
#include <WebServer.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include "esp_camera.h"
#include <HTTPClient.h>
#include <base64.h>


//======================================== CAMERA_MODEL_AI_THINKER GPIO.
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// LED Flash PIN (GPIO 4)
#define FLASH_LED_PIN 4             

// Thông tin WiFi
const char* ssid = "Banh Mi";
const char* password = "banhbao2022";

// Địa chỉ máy chủ (máy tính chạy XAMPP)
String serverName = "192.168.1.7";
String serverPath = "/php/ESP32CAM/upload_img.php";
const int serverPort = 80;

// Web server ESP32-CAM (HTTP)
WebServer server(80);

// Cờ để bật/tắt đèn flash khi chụp
bool LED_Flash_ON = true;

//============================== Hàm gửi ảnh về server
void sendPhotoToServer() {
  String AllData;
  String DataBody;

  Serial.println();
  Serial.println("-----------");
  Serial.println("Taking a photo...");

  if (LED_Flash_ON) {
    digitalWrite(FLASH_LED_PIN, HIGH);
    delay(1000);
  }

  for (int i = 0; i <= 3; i++) {
    camera_fb_t * fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      ESP.restart();
      return;
    }
    esp_camera_fb_return(fb);
    delay(200);
  }

  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    ESP.restart();
    return;
  }

  if (LED_Flash_ON) digitalWrite(FLASH_LED_PIN, LOW);
  Serial.println("Taking a photo was successful.");
  Serial.println("Connecting to server: " + serverName);

  WiFiClient client;
  if (client.connect(serverName.c_str(), serverPort)) {
    Serial.println("Connection successful!");

    String post_data = "--dataMarker\r\nContent-Disposition: form-data; name=\"imageFile\"; filename=\"ESP32CAMCap.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n";
    String head = post_data;
    String boundary = "\r\n--dataMarker--\r\n";

    uint32_t imageLen = fb->len;
    uint32_t dataLen = head.length() + boundary.length();
    uint32_t totalLen = imageLen + dataLen;

    client.println("POST " + serverPath + " HTTP/1.1");
    client.println("Host: " + serverName);
    client.println("Content-Length: " + String(totalLen));
    client.println("Content-Type: multipart/form-data; boundary=dataMarker");
    client.println();
    client.print(head);

    uint8_t *fbBuf = fb->buf;
    size_t fbLen = fb->len;
    for (size_t n = 0; n < fbLen; n += 1024) {
      if (n + 1024 < fbLen) {
        client.write(fbBuf, 1024);
        fbBuf += 1024;
      } else if (fbLen % 1024 > 0) {
        size_t remainder = fbLen % 1024;
        client.write(fbBuf, remainder);
      }
    }
    client.print(boundary);
    esp_camera_fb_return(fb);

    int timoutTimer = 10000;
    long startTimer = millis();
    boolean state = false;
    Serial.println("Response : ");
    while ((startTimer + timoutTimer) > millis()) {
      Serial.print(".");
      delay(200);

      while (client.available()) {
        char c = client.read();
        if (c == '\n') {
          if (AllData.length() == 0) { state = true; }
          AllData = "";
        } else if (c != '\r') {
          AllData += String(c);
        }
        if (state == true) {
          DataBody += String(c);
        }
        startTimer = millis();
      }
      if (DataBody.length() > 0) break;
    }

    client.stop();
    Serial.println(DataBody);
    Serial.println("-----------");
    Serial.println();

  } else {
    client.stop();
    Serial.println("Connection to server failed.");
    Serial.println("-----------");
  }
}

//============================== Hàm xử lý khi truy cập /capture
void handleCapture() {
  sendPhotoToServer();
  server.send(200, "text/plain", "Photo captured and sent to server.");
}

//============================== Setup
void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Tắt lỗi brownout

  Serial.begin(115200);
  Serial.println();

  pinMode(FLASH_LED_PIN, OUTPUT);
  WiFi.mode(WIFI_STA);
  Serial.print("Connecting to: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  int timeout = 20 * 2; // 20s timeout
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
    if (--timeout == 0) {
      Serial.println("\nFailed to connect. Restarting...");
      ESP.restart();
    }
  }

  Serial.println();
  Serial.print("Connected! IP: ");
  Serial.println(WiFi.localIP());

  // Cấu hình camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if(psramFound()){
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 20;
  config.fb_count = 1;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 20;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    delay(1000);
    ESP.restart();
  }

  sensor_t * s = esp_camera_sensor_get();
  s->set_framesize(s, FRAMESIZE_QVGA);

  Serial.println("Camera ready.");

  // Bắt đầu web server
  server.on("/capture", handleCapture);
  server.begin();
  Serial.println("Web server started. Truy cập http://<ESP32_IP>/capture để chụp ảnh.");
}

//============================== Loop
void loop() {
  server.handleClient();
}
