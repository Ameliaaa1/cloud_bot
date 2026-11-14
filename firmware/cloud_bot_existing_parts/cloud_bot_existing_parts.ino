// Existing ESP32-CAM + MB + USB only. Espressif Arduino core 3.x.
// No external libraries, strip, SD, pump, mist or touch wiring.
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "esp_camera.h"
#include "web_app.h"

WebServer server(80);
bool cameraReady = false;
String weather = "cloudy";
String controlMode = "auto";
String proposal = "cloudy";
bool autoOnline = false;
uint32_t lastAuto = 0, lastPulse = 0;
bool mistSim = false;

// Hardware outputs deliberately remain disabled until matching drivers are fitted.
// This scheduler simulates at most one 300 ms mist pulse per 60 seconds.
void updateOutputs() {
  const uint32_t now = millis();
  if (autoOnline && uint32_t(now-lastAuto)>10000) {
    autoOnline=false;
    if (controlMode=="auto") weather="cloudy";
  }
  if (weather!="rainy") mistSim=false;
  else if (uint32_t(now-lastPulse)>=60000) { lastPulse=now;mistSim=true; }
  if (mistSim && uint32_t(now-lastPulse)>=300) mistSim=false;
}

const char PAGE[] PROGMEM = R"CLOUDBOT(
<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>cloud_bot</title><style>
*{box-sizing:border-box}body{margin:0;background:#edf1f4;color:#111;font:16px system-ui}main{max-width:740px;margin:30px auto;padding:24px}button{padding:12px 18px;margin:5px;border:1px solid #888;border-radius:12px;background:white;color:#111;font:inherit;cursor:pointer}button[aria-pressed=true]{border:3px solid #19495a;background:#d9edf4}button:disabled{opacity:.5}.scene{height:240px;display:grid;place-items:center;background:#dce4ea;border-radius:24px;font-size:100px}.scene[data-weather=sunny]{background:#fff0c9}.scene[data-weather=rainy]{background:#b5c2cd}.panel{background:white;padding:18px;margin-top:16px;border-radius:18px}p{line-height:1.7}img{max-width:100%;width:320px}#status{min-height:28px}small{color:#333}
</style><main><h1>cloud_bot</h1><p>一朵云，陪你照顾一株小植物。</p><div id="scene" class="scene" role="img" aria-label="阴天">☁️</div>
<div id="controls"><button data-control="auto">自动识别</button><button data-weather="sunny">晴天</button><button data-weather="cloudy">阴天</button><button data-weather="rainy">雨天</button></div><p id="status" role="status">正在连接…</p>
<div class="panel"><strong>输出预览</strong><p id="outputs">等待设备状态</p><small>灯光与喷雾目前为软件模拟，实体输出尚未启用。</small></div>
<div class="panel"><strong>设备摄像头</strong><p>电脑表情识别使用电脑摄像头；下面是 ESP32 镜头的独立取景。</p><button id="camera">开启预览</button><br><img id="photo" hidden alt="设备摄像头画面"><p id="cameraStatus" role="status"></p></div>
<p><small>表情只作为互动线索。图像在本地处理，程序不保存或上传照片。</small></p></main>
<script src="/app.js"></script></html>
)CLOUDBOT";

bool initCamera() {
  camera_config_t c = {};
  c.ledc_channel = LEDC_CHANNEL_0; c.ledc_timer = LEDC_TIMER_0;
  c.pin_d0 = 5; c.pin_d1 = 18; c.pin_d2 = 19; c.pin_d3 = 21;
  c.pin_d4 = 36; c.pin_d5 = 39; c.pin_d6 = 34; c.pin_d7 = 35;
  c.pin_xclk = 0; c.pin_pclk = 22; c.pin_vsync = 25; c.pin_href = 23;
  c.pin_sccb_sda = 26; c.pin_sccb_scl = 27;
  c.pin_pwdn = 32; c.pin_reset = -1; c.xclk_freq_hz = 20000000;
  c.pixel_format = PIXFORMAT_JPEG; c.frame_size = FRAMESIZE_QVGA;
  c.jpeg_quality = 15; c.fb_count = 1; c.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  c.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  const esp_err_t err = esp_camera_init(&c);
  if (err != ESP_OK) {
    Serial.printf("Camera failed: 0x%x. Weather controls still available.\n", err);
    return false;
  }
  return true;
}

String stateJson() {
  updateOutputs();
  String out="{\"version\":2,\"weather\":\""+weather+"\",\"control\":\""+controlMode+"\",\"camera\":"+(cameraReady?"true":"false");
  out+=",\"auto_online\":"+String(autoOnline?"true":"false")+",\"outputs\":{\"hardware_enabled\":false,\"light\":\""+weather+"\",\"mist_simulated\":"+String(mistSim?"true":"false")+"}}";
  return out;
}

void sendState() {
  server.sendHeader("Cache-Control", "no-store");
  server.send(200,"application/json",stateJson());
}

void setup() {
  Serial.begin(115200);
  pinMode(4, OUTPUT); digitalWrite(4, LOW); // Bright flash stays off.
  cameraReady = initCamera();
  WiFi.mode(WIFI_AP);
  if (!WiFi.softAP("cloud_bot", "set-a-local-password")) Serial.println("AP failed; restart board.");
  server.on("/", HTTP_GET, []() { server.send_P(200, "text/html; charset=utf-8", PAGE); });
  server.on("/state", HTTP_GET, sendState);
  server.on("/app.js", HTTP_GET, []() { server.send_P(200,"application/javascript; charset=utf-8",APP_JS); });
  server.on("/control", HTTP_POST, []() {
    const String value=server.arg("mode");
    if (value!="auto" && value!="manual") { server.send(400,"text/plain","Invalid control");return; }
    controlMode=value;
    if (value=="auto") weather=autoOnline?proposal:"cloudy";
    sendState();
  });
  server.on("/weather", HTTP_POST, []() {
    const String requested=server.arg("mode"), source=server.arg("source");
    if (requested!="sunny" && requested!="cloudy" && requested!="rainy") { server.send(400,"text/plain","Invalid weather");return; }
    if (source!="" && source!="manual" && source!="auto") { server.send(400,"text/plain","Invalid source");return; }
    if (source=="auto") {
      proposal=requested;lastAuto=millis();autoOnline=true;
      if (controlMode=="auto") weather=requested;
    } else { controlMode="manual";weather=requested; }
    Serial.println("Weather: "+weather+" / "+controlMode);sendState();
  });
  server.on("/capture", HTTP_GET, []() {
    if (!cameraReady) { server.send(503, "text/plain", "Camera unavailable"); return; }
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) { server.send(503, "text/plain", "Capture failed"); return; }
    server.sendHeader("Cache-Control", "no-store"); server.setContentLength(fb->len);
    server.send(200, "image/jpeg", "");
    auto client = server.client(); size_t sent = 0; const uint32_t started = millis();
    while (sent < fb->len && client.connected() && millis() - started < 3000) {
      size_t count = client.write(fb->buf + sent, min(size_t(1024), fb->len - sent));
      if (!count) break;
      sent += count; delay(0);
    }
    if (sent != fb->len) client.stop();
    esp_camera_fb_return(fb);
  });
  server.onNotFound([]() { server.send(404, "text/plain", "Not found"); });
  server.begin(); Serial.println("Wi-Fi: cloud_bot / password: set-a-local-password");
  Serial.print("Open http://"); Serial.println(WiFi.softAPIP());
}

void loop() {
  updateOutputs();server.handleClient();
  if (Serial.available() && Serial.read()=='?') Serial.println(stateJson());
  delay(2);
}

