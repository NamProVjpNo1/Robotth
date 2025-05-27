#include <WiFi.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include "esp_camera.h"
//======================================== 

#define TRIGGER_PIN 14

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
//======================================== 

#define FLASH_LED_PIN 15

//======================================== Thông tin WiFi
const char* ssid = "Banh Mi";
const char* password = "banhbao2022";
//======================================== 

// Thông tin server
String serverName = "192.168.1.7";
String serverPath = "/php/ESP32CAM/upload_img.php";
const int serverPort = 80;

// Cấu hình flash
bool LED_Flash_ON = true;

// Khởi tạo WiFiClient
WiFiClient client;

//________________________________________________________________________________ sendPhotoToServer()
bool sendPhotoToServer() {
  String AllData;
  String DataBody;
  bool success = false;

  Serial.println();
  Serial.println("-----------");
 
  Serial.print("Kiểm tra tín hiệu WiFi (RSSI): ");
  Serial.println(WiFi.RSSI());

  //---------------------------------------- Chụp ảnh
  Serial.println("Đang chụp ảnh...");

  if (LED_Flash_ON == true) {
    digitalWrite(FLASH_LED_PIN, HIGH);
    delay(1000);
  }
  
  // Chụp thử vài lần để camera ổn định
  for (int i = 0; i <= 3; i++) {
    camera_fb_t * fb = NULL;
    fb = esp_camera_fb_get();
    if(!fb) {
      Serial.println("Chụp ảnh thất bại");
      if (LED_Flash_ON == true) digitalWrite(FLASH_LED_PIN, LOW);
      esp_camera_fb_return(fb);
      return false;
    } 
    esp_camera_fb_return(fb);
    delay(200);
  }
  
  // Chụp ảnh thật
  camera_fb_t * fb = NULL;
  fb = esp_camera_fb_get();
  if(!fb) {
    Serial.println("Chụp ảnh thất bại");
    if (LED_Flash_ON == true) digitalWrite(FLASH_LED_PIN, LOW);
    return false;
  } 

  if (LED_Flash_ON == true) digitalWrite(FLASH_LED_PIN, LOW);
  
  Serial.println("Chụp ảnh thành công.");
  Serial.print("Kích thước ảnh: ");
  Serial.print(fb->len);
  Serial.println(" bytes");

  //---------------------------------------- Kết nối và gửi ảnh đến server

  Serial.println("Đang kết nối đến server: " + serverName);

  // Tăng timeout kết nối lên 15 giây
  if (client.connect(serverName.c_str(), serverPort, 15000)) {
    Serial.println("Kết nối thành công!");   
     
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
    for (size_t n=0; n<fbLen; n=n+1024) {
      if (n+1024 < fbLen) {
        client.write(fbBuf, 1024);
        fbBuf += 1024;
      }
      else if (fbLen%1024>0) {
        size_t remainder = fbLen%1024;
        client.write(fbBuf, remainder);
      }
    }   
    client.print(boundary);
    
    esp_camera_fb_return(fb);
   
    int timoutTimer = 20000;
    long startTimer = millis();
    boolean state = false;
    Serial.println("Phản hồi từ server:");
    while ((startTimer + timoutTimer) > millis()) {
      Serial.print(".");
      delay(200);
         
      // Bỏ qua HTTP headers
      while (client.available()) {
        char c = client.read();
        if (c == '\n') {
          if (AllData.length()==0) { state=true; }
          AllData = "";
        }
        else if (c != '\r') { AllData += String(c); }
        if (state==true) { DataBody += String(c); }
        startTimer = millis();
      }
      if (DataBody.length()>0) { break; }
    }
    client.stop();
    Serial.println(DataBody);
    
    // Kiểm tra phản hồi từ server để xác định thành công
    if (DataBody.indexOf("successfully uploaded") > 0) {
      Serial.println("Tải ảnh lên server thành công!");
      success = true;
    } else {
      Serial.println("Tải ảnh lên server thất bại!");
      success = false;
    }
    
    Serial.println("-----------");
    Serial.println();
    
    return success;
  }
  else {
    client.stop();
    Serial.println("Kết nối đến " + serverName + " thất bại.");
    Serial.println("WiFi status: " + String(WiFi.status()));
    Serial.println("ESP32-CAM IP: " + WiFi.localIP().toString());
    Serial.println("-----------");
    esp_camera_fb_return(fb);
    return false;
  }
}
//________________________________________________________________________________ 

//________________________________________________________________________________ VOID SETUP()
void setup() {
  // Tắt brownout detector
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  
  Serial.begin(115200);
  pinMode(TRIGGER_PIN, INPUT_PULLUP);
  Serial.println();

  pinMode(FLASH_LED_PIN, OUTPUT);

  // Thiết lập ESP32 WiFi ở chế độ station
  WiFi.mode(WIFI_STA);
  Serial.println();

  //---------------------------------------- Kết nối WiFi
  Serial.println();
  Serial.print("Đang kết nối tới: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
  // Timeout kết nối là 20 giây
  int connecting_process_timed_out = 20;
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
    connecting_process_timed_out--;
    if(connecting_process_timed_out == 0) {
      Serial.println();
      Serial.print("Không thể kết nối tới ");
      Serial.println(ssid);
      Serial.println("Khởi động lại ESP32 CAM.");
      delay(1000);
      ESP.restart();
    }
  }

  Serial.println();
  Serial.print("Đã kết nối thành công tới ");
  Serial.println(ssid);
  Serial.print("Địa chỉ IP của ESP32-CAM: ");
  Serial.println(WiFi.localIP());
  //---------------------------------------- 
  Serial.println();
  Serial.printf("Free RAM: %d bytes\n", esp_get_free_heap_size());
  //---------------------------------------- Thiết lập camera
  Serial.println();
  Serial.print("Đang cấu hình camera ESP32 CAM...");
  
  
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

  // Khởi tạo với thông số cao
  if(psramFound()){
  config.frame_size = FRAMESIZE_HQVGA;
  config.jpeg_quality = 22;
  config.fb_count = 1;
  } else {
    config.frame_size = FRAMESIZE_HQVGA;
    config.jpeg_quality = 22;
    config.fb_count = 1;
  }
  
  // Khởi tạo camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Khởi tạo camera thất bại với lỗi 0x%x", err);
    Serial.println();
    digitalWrite(FLASH_LED_PIN, LOW);
    Serial.println("Khởi động lại ESP32 CAM.");
    delay(1000);
    ESP.restart();
  }

  sensor_t * s = esp_camera_sensor_get();

  // Thiết lập độ phân giải
  s->set_framesize(s, FRAMESIZE_HQVGA); // UXGA|SXGA|XGA|SVGA|VGA|CIF|QVGA|HQVGA|QQVGA

  Serial.println();
  Serial.println("Cấu hình camera ESP32 CAM thành công.");
  //---------------------------------------- 

  Serial.println();
  Serial.println("ESP32-CAM sẽ chụp ảnh liên tục cho đến khi gửi thành công.");
}
//________________________________________________________________________________ 

void loop() {
  if (digitalRead(TRIGGER_PIN) == HIGH) {
    Serial.println("Nhận tín hiệu trigger. Đang chụp ảnh...");
    bool success = sendPhotoToServer();
    if (success) {
      Serial.println("Chụp và gửi ảnh thành công.");
    } else {
      Serial.println("Chụp hoặc gửi ảnh thất bại.");
    }
    delay(5000);
  }

  delay(100);
}
