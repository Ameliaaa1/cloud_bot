// Existing ESP32-CAM + MB + USB only. Espressif Arduino core 3.x.
// No external libraries, strip, SD, pump, mist or touch wiring.
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "esp_camera.h"

WebServer server(80);
bool cameraReady = false;
String weather = "cloudy";
const char PAGE[] PROGMEM = R"CLOUDBOT(
<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>cloud_bot · 桌面陪伴原型</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f0f3f6;color:#344154;font:16px system-ui,sans-serif}
main{max-width:760px;margin:32px auto;padding:24px}h1{font-size:30px;margin-bottom:6px}p{line-height:1.7}.sub{color:#667486}
.scene{height:300px;position:relative;overflow:hidden;border-radius:28px;background:#e1e7ed;transition:background 2s}
.sun{position:absolute;left:55%;top:35px;width:65px;height:65px;border-radius:50%;background:#ffd585;opacity:0;transition:opacity 2s}
.cloud{position:absolute;top:75px;left:50%;width:180px;height:68px;transform:translateX(-50%);border-radius:70px;background:#abb7c4;animation:float 4s ease-in-out infinite;transition:background 2s}
.cloud:before,.cloud:after{content:'';position:absolute;background:inherit;border-radius:50%}.cloud:before{width:90px;height:90px;left:24px;top:-40px}.cloud:after{width:75px;height:75px;right:15px;top:-25px}
.face{position:absolute;z-index:1;left:63px;top:22px;font-size:22px;letter-spacing:8px}
.rain{position:absolute;left:50%;top:154px;transform:translateX(-50%);display:flex;gap:22px;opacity:0;transition:opacity 1s}
.rain i{width:2px;height:13px;background:#9bb7c8;border-radius:4px;animation:fall 1.2s infinite}.rain i:nth-child(2n){animation-delay:-.6s}
.plant{position:absolute;bottom:14px;left:50%;transform:translateX(-50%);font-size:58px}
.scene[data-weather=sunny]{background:#f8edda}.scene[data-weather=sunny] .cloud{background:#fffdf8}.scene[data-weather=sunny] .sun{opacity:1}
.scene[data-weather=rainy]{background:#d4dde5}.scene[data-weather=rainy] .cloud{background:#82909f}.scene[data-weather=rainy] .rain{opacity:1}
.controls{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}button{border:1px solid #b3bdca;background:white;color:#344154;border-radius:12px;padding:12px 18px;font:inherit;cursor:pointer}
button[aria-pressed=true]{background:#344154;color:white}button:focus-visible{outline:3px solid #9a7200;outline-offset:3px}
.panel{background:white;border-radius:20px;padding:20px;margin-top:18px}img{display:block;width:100%;max-width:320px;border-radius:12px;margin:12px 0}img[hidden]{display:none}
#status{min-height:28px}small{color:#667486}@keyframes float{50%{transform:translate(-50%,-7px)}}@keyframes fall{to{transform:translateY(45px);opacity:0}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style><main><h1>cloud_bot</h1><p class="sub">一朵云，陪你照顾一株小植物。</p>
<div class="scene" data-weather="cloudy" id="scene" role="img" aria-label="阴天的云朵"><div class="sun"></div><div class="cloud"><span class="face">•ᴗ•</span></div><div class="rain"><i></i><i></i><i></i><i></i><i></i></div><div class="plant">🪴</div></div>
<div class="controls"><button data-mode="sunny">晴天</button><button data-mode="cloudy">阴天</button><button data-mode="rainy">下雨</button></div>
<p id="status" role="status">正在连接设备…</p>
<div class="panel"><strong>摄像头预览</strong><p>默认关闭。开启后约每秒刷新一张照片，可随时停止。</p><button id="camera" aria-pressed="false">开启预览</button><img id="photo" alt="ESP32-CAM 拍摄画面" hidden><p id="cameraStatus" role="status"></p></div>
<p><small>当前为手动天气互动＋摄像头取景，尚未加入表情识别。雨和盆栽为屏幕模拟效果；没有驱动实体灯带、喷雾或水泵。程序不保存照片，不上传云端。</small></p>
</main><script>
const scene=document.getElementById('scene'),statusLine=document.getElementById('status');
const names={sunny:'晴天',cloudy:'阴天',rainy:'雨天'};
function render(mode){scene.dataset.weather=mode;scene.setAttribute('aria-label',names[mode]+'的云朵');document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));}
let busy=false;
async function sync(mode){if(busy)return;busy=true;const abort=new AbortController(),timeout=setTimeout(()=>abort.abort(),5000);try{const response=await fetch(mode?'/weather':'/state',{method:mode?'POST':'GET',headers:mode?{'Content-Type':'application/x-www-form-urlencoded'}:{},body:mode?'mode='+encodeURIComponent(mode):undefined,signal:abort.signal});if(!response.ok)throw Error();const state=await response.json();render(state.weather);statusLine.textContent='设备已连接 · '+names[state.weather];}catch(e){statusLine.textContent='连接中断，请检查 cloud_bot Wi-Fi，然后刷新页面。';}finally{clearTimeout(timeout);busy=false;}}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>sync(b.dataset.mode));
const photo=document.getElementById('photo'),cameraButton=document.getElementById('camera'),cameraStatus=document.getElementById('cameraStatus');
let preview=false,timer;
function capture(){if(preview)photo.src='/capture?t='+Date.now();}
function schedule(){clearTimeout(timer);if(preview)timer=setTimeout(capture,1000);}
photo.onload=()=>{if(preview){cameraStatus.textContent='预览中 · 点击停止即可暂停取景';schedule();}};
photo.onerror=()=>{if(preview){cameraStatus.textContent='取景失败，请检查串口日志、摄像头排线或 USB 供电。';schedule();}};
cameraButton.onclick=()=>{preview=!preview;clearTimeout(timer);photo.hidden=!preview;cameraButton.textContent=preview?'停止预览':'开启预览';cameraButton.setAttribute('aria-pressed',String(preview));cameraStatus.textContent=preview?'正在取景…':'预览已停止';if(preview)capture();else photo.removeAttribute('src');};
sync();setInterval(()=>sync(),3000);
</script></html>
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

void sendState() {
  server.sendHeader("Cache-Control", "no-store");
  server.send(200, "application/json", "{\"weather\":\"" + weather + "\",\"camera\":" + (cameraReady ? "true" : "false") + "}");
}

void setup() {
  Serial.begin(115200);
  pinMode(4, OUTPUT); digitalWrite(4, LOW); // Bright flash stays off.
  cameraReady = initCamera();
  WiFi.mode(WIFI_AP);
  if (!WiFi.softAP("cloud_bot", "set-a-local-password")) Serial.println("AP failed; restart board.");
  server.on("/", HTTP_GET, []() { server.send_P(200, "text/html; charset=utf-8", PAGE); });
  server.on("/state", HTTP_GET, sendState);
  server.on("/weather", HTTP_POST, []() {
    const String requested = server.arg("mode");
    if (requested != "sunny" && requested != "cloudy" && requested != "rainy") {
      server.send(400, "text/plain", "Invalid weather"); return;
    }
    weather = requested; Serial.println("Weather: " + weather); sendState();
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

void loop() { server.handleClient(); delay(2); }


