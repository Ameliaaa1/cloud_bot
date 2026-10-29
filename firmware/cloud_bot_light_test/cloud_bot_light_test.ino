// cloud_bot: ESP32-CAM + external 12V WS2811 strip, light-only bench test.
// Requires FastLED. No camera, SD card, mist maker or pump is initialized.
// GPIO13 is shared with microSD: remove the card and do not initialize SD.
#include <FastLED.h>

constexpr uint8_t DATA_PIN = 13;
// Photo suggests 3 physical LEDs per addressable group: 30 / 3 = 10.
constexpr uint16_t NUM_GROUPS = 10;
constexpr uint8_t MAX_BRIGHTNESS = 32; // 32/255; start dim.
CRGB leds[NUM_GROUPS];
enum class Weather { Off, Sunny, Cloudy, Rainy, Red, Green, Blue, Chase };
Weather weather = Weather::Off;
uint32_t lastFrame = 0;

void showHelp() {
  Serial.println("cloud_bot LIGHT ONLY: s=sunny c=cloudy r=rain light x=off");
  Serial.println("1=red 2=green 3=blue t=group chase h=help");
}

void setup() {
  Serial.begin(115200);
  FastLED.addLeds<WS2811, DATA_PIN, RGB>(leds, NUM_GROUPS);
  FastLED.setBrightness(MAX_BRIGHTNESS);
  FastLED.clear(true);
  showHelp();
}

void loop() {
  while (Serial.available()) {
    const char command = Serial.read();
    bool accepted = true;
    switch (command) {
      case 's': weather = Weather::Sunny; break;
      case 'c': weather = Weather::Cloudy; break;
      case 'r': weather = Weather::Rainy; break;
      case 'x': weather = Weather::Off; break;
      case '1': weather = Weather::Red; break;
      case '2': weather = Weather::Green; break;
      case '3': weather = Weather::Blue; break;
      case 't': weather = Weather::Chase; break;
      case 'h': showHelp(); accepted = false; break;
      default: accepted = false; break;
    }
    if (accepted) { Serial.print("Mode: "); Serial.println(command); }
  }

  const uint32_t now = millis();
  if (now - lastFrame < 30) return;
  lastFrame = now;
  fill_solid(leds, NUM_GROUPS, CRGB::Black);
  switch (weather) {
    case Weather::Sunny:
      fill_solid(leds, NUM_GROUPS, CRGB(255, 190, 100)); break;
    case Weather::Cloudy:
      fill_solid(leds, NUM_GROUPS, CRGB(55, 65, 80)); break;
    case Weather::Rainy:
      // A slow, gentle lighting change, not an actual mist command.
      fill_solid(leds, NUM_GROUPS, CRGB(40, 55, 90));
      for (uint16_t i = 0; i < NUM_GROUPS; ++i) {
        leds[i].nscale8_video(beatsin8(8, 100, 180));
      }
      break;
    case Weather::Red: fill_solid(leds, NUM_GROUPS, CRGB::Red); break;
    case Weather::Green: fill_solid(leds, NUM_GROUPS, CRGB::Green); break;
    case Weather::Blue: fill_solid(leds, NUM_GROUPS, CRGB::Blue); break;
    case Weather::Chase:
      leds[(now / 700) % NUM_GROUPS] = CRGB(100, 100, 100); break;
    case Weather::Off: break;
  }
  FastLED.show();
}

