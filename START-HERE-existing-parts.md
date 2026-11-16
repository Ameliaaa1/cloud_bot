# cloud_bot: Start with the Existing Parts Only

This version validates image capture, device communication, and weather interaction. Weather animations appear on a computer or phone screen. For computer-based facial-expression control, see the [software v2 guide](EMOTION-CONTROL-README.md).

## What You Need

- ESP32-CAM and MB baseboard.
- A data-capable Micro-USB cable and a computer.

No ESP8266 or external wiring is required. Leave the 12V LED strip disconnected for now; add the blue touch module only after confirming its model. If the existing cable is charging-only, use an available data cable to upload firmware.

## Steps

1. With power disconnected, seat the ESP32-CAM on the MB baseboard, matching the 5V, GND, and other pin positions on both boards. Do not reverse it or offset it by a row. Remove the SD card and leave other components disconnected.
2. Connect to the computer with a USB data cable. Keep the underside away from metal and place the board on a flat, nonconductive support.
3. In Arduino IDE's Boards Manager, install the esp32 package from Espressif Systems (the code targets 3.x). Select AI Thinker ESP32-CAM and the actual serial port. No additional libraries such as FastLED are needed. If no port appears, check the data cable and the appropriate CH340 serial driver.
4. Open firmware/cloud_bot_existing_parts/cloud_bot_existing_parts.ino, verify compilation, then upload. Close Serial Monitor during upload.
5. If upload remains at Connecting, try holding the baseboard's IO0 button, pressing and releasing RST, then releasing IO0 before uploading again. After upload, press RST without holding IO0 to boot normally. This applies to the common IO0/RST baseboard shown in the photos; follow the baseboard's instructions if its buttons behave differently.
6. Open Serial Monitor at 115200 baud to view logs.
7. Connect the computer or phone to the device Wi-Fi: network cloud_bot, password set-a-local-password. The hotspot has no internet access; choose to stay connected when warned.
8. Open http://192.168.4.1 in the browser address bar (use the logged address if different). HTTPS is not required.
9. Click the sunny, cloudy, and rainy controls to observe the cloud changing. Starting preview captures roughly one image per second; stopping preview pauses image requests.

If the computer has no Wi-Fi, connect a phone to the device hotspot while the computer continues supplying USB power. Stopping preview stops new photo requests, but the camera remains initialized. Unplug USB to turn it off completely. The program does not save photos or upload them to the cloud.

## Verification and Troubleshooting

- Confirm the hotspot appears, the page opens, and weather switching produces corresponding Weather messages in the serial log.
- Confirm preview displays an image and stopping it stops requests for new photos.
- Weather buttons remain usable if camera initialization fails. Inspect the serial error and check the board model, ribbon cable, and power supply.
- After a restart, weather returns to cloudy and preview is off by default.

Compilation, upload, and web functionality of the v2 firmware have been verified on an AI Thinker ESP32-CAM; see the [software validation record](SOFTWARE-VALIDATION.md). Preserve the complete error message if a problem occurs. For repeated resets, check the USB cable and power first.

The next stage is to validate the physical cloud shell, LED strip, misting, and drip irrigation.

Camera pin assignments and initialization follow Espressif's official CameraWebServer example:
https://github.com/espressif/arduino-esp32/tree/master/libraries/ESP32/examples/Camera/CameraWebServer
