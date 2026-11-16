# cloud_bot Stage One: Lighting Test with the Existing ESP32-CAM

## Confirmed and Unconfirmed Details

Physical photos clearly show the strip's 12V, DI, DO, GND, and arrow markings. Its appearance suggests a WS2811-type strip with external driver chips and three LEDs per group; the packaging also says WS2811. Initially test the half-meter, 30-LED strip as 10 addressable groups, then verify by lighting each group individually. The exact chip revision and RGB order have not been verified by powering the physical strip.

The user does not have an ESP8266. The earlier dual-controller design is a later expansion option, not a prerequisite for this test. Use the existing ESP32-CAM and ESP32-CAM-MB without enabling the camera or SD card. Camera integration must be validated separately.

## Additional Materials for This Test

- Regulated 12V DC adapter: 12V/2A is an initial option for this half-meter section, provided its rated power does not exceed the supply's capacity. This is not a power-supply specification for the complete device.
- Matching power-socket adapter cable or screw terminals, with appropriate branch fuse protection.
- SN74AHCT125 level-shifter module: it must expose 5V/VCC, GND, A input, Y output, and enable, or have enable correctly fixed. Do not substitute a common bidirectional I²C level-shifter board.
- 12V→5V buck converter: in this test it powers only the level-shifter module. Adjust to 5.0V with a multimeter first. The development board remains powered by USB through the MB baseboard.
- 330Ω series resistor, approximately 470–1000µF/25V electrolytic capacitor, 100nF decoupling capacitor (not needed separately if included on the module), wires, and reliable connectors.
- Micro-USB data cable and multimeter. Soldering is required if the pads have no attached wires. Do not power the strip by pressing bare jumper-pin ends against solder pads.

## Wiring Table (Disconnect All Power Before Wiring)

| From | To |
|---|---|
| 12V supply positive, through branch protection | Strip input 12V; buck-converter IN+ |
| 12V supply negative | Strip GND; buck-converter IN- |
| Buck-converter OUT+, measured at 5.0V | AHCT125 module VCC/5V |
| Buck-converter OUT- | AHCT125 GND; ESP32-CAM GND |
| ESP32-CAM pin marked IO13 | AHCT125 1A (or A of the selected channel) |
| 1Y of the same channel | Through 330Ω resistor to strip DI |
| /1OE of the same channel (active low) | GND; follow the module instructions if enable is already fixed |
| Computer USB | ESP32-CAM-MB Micro-USB |

Connect the electrolytic capacitor's positive terminal to strip 12V and negative terminal to strip GND, close to the strip input. Connect the AHCT125's 100nF decoupling capacitor between VCC and GND. For a bare chip or module with untreated unused inputs, handle those inputs according to the manufacturer's instructions; do not leave them floating. If unfamiliar with this, choose an assembled module with clearly labeled connections.

The supply negative, controller GND, and level-shifter GND share ground. Do not connect the two 5V positive rails. Never connect 12V to ESP32-CAM IO, 5V, or 3V3. The meaning of the board's VCC pin has not been verified; do not use it.

In the photo's current orientation, the three tinned pads at the bottom of the strip are left 12V, center DI, and right GND. Follow the printed labels above them rather than guessing from how the strip is held. Arrows point from the input toward subsequent LED groups. DO is an output and cannot serve as the control-signal input.

GPIO13 is not part of the official AI Thinker camera pin mapping, but it is shared with microSD. Remove the SD card and leave SD uninitialized for this test. Do not use GPIO4 to drive the strip, to avoid involving the onboard bright flash LED. Running camera and strip together later still requires timing, power, and stability tests.

## Upload and Test

1. Keep strip 12V disconnected. Seat the boards on the MB baseboard by matching pin names and checking orientation; do not infer orientation solely from the USB connector. Connect USB to the computer.
2. Install Espressif's esp32 board support and the FastLED library in Arduino IDE. Initially select AI Thinker ESP32-CAM (matching the common physical layout) and the correct serial port.
3. Open firmware/cloud_bot_light_test/cloud_bot_light_test.ino, verify compilation, and upload. If it cannot enter download mode automatically, use IO0/RST as specified by the MB baseboard instructions. Restore normal boot afterward; do not leave IO0 grounded.
4. Disconnect all power and complete the wiring above. Check capacitor polarity, 5V buck output, and absence of a short between 12V and GND.
5. Power the controller through USB first and open Serial Monitor at 115200 baud. The program sends all-off data by default. Then power the 12V branch supplying the strip and level shifter, and send x.
6. Send 1, 2, and 3 in sequence to check red, green, and blue. If the order is wrong, change only the RGB-order argument to addLeds (such as GRB or BRG), not the power wiring.
7. Send t to check whether each step lights a three-LED group and whether all LEDs are covered. Adjust NUM_GROUPS if the group count differs.
8. Send s/c/r for sunny, cloudy, and rainy lighting; send x to turn it off. This version does not control a misting module or water pump.
9. If the strip stays dark, disconnect power and check DI/DO, common ground, level-shifter enable, and the supply. Do not start by setting full brightness. If the final group is affected by a random power-on state, send x again or disconnect power to investigate.
10. Run stable lighting for 30 minutes while observing temperature rise, flicker, and resets. At the end, send x, disconnect strip 12V first, then disconnect USB.

At the time of this test record, arduino-cli was not found in the environment, so compilation was not performed, and no physical hardware was connected for upload or power-on testing. The code is an initial version pending board-level validation. Save compilation errors and test results before making adjustments.

## References

- FastLED official documentation: https://fastled.io/docs/
- WLED wiring and AHCT125 guidance: https://kno.wled.ge/basics/wiring-guides/
- Espressif camera pins: https://github.com/espressif/arduino-esp32/blob/master/libraries/ESP32/examples/Camera/CameraWebServer/camera_pins.h
