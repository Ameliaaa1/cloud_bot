# cloud_bot Physical Prototype V0.1

Current execution plan: prioritize the existing ESP32-CAM, MB baseboard, and USB data cable to run camera and browser-based weather interaction first, without requiring additional purchases. Start with START-HERE-existing-parts.md; the program is firmware/cloud_bot_existing_parts/cloud_bot_existing_parts.ino. The LED strip, dual-board arrangement, and water-system purchases described here are plans for later stages.

Goal: build a desktop prototype that changes weather through buttons or computer commands, produces real mist, and dispenses measured amounts of water to the plant below. Add camera-based facial-expression input afterward.

Latest physical-inventory correction: the user does not have an ESP8266; the earlier inventory inference based on an order was incorrect. Photos have confirmed the existing ESP32-CAM and MB baseboard, and the strip itself is marked 12V, DI, DO, and GND. Stage one now uses ESP32-CAM GPIO13 for a standalone lighting test; see light-test-wiring.md and firmware/cloud_bot_light_test/cloud_bot_light_test.ino. The ESP8266 dual-board design below is retained as a historical expansion option, not a required purchase. Reassess whether to add a standard ESP32 development board at the misting and drip-irrigation stage.

This document is a design plan, not a record of completed hardware wiring, fabrication, or program validation. Dimensions and timing values are initial experimental parameters and must be revised through physical testing.

## 1. Existing Parts and Roles

The following identifications came from order screenshots supplied by the user and do not replace checking the physical models:

| Part | Identification | Prototype role |
|---|---|---|
| ESP32-CAM and programming baseboard | Explicitly listed in the order; exact board model to be checked | Supply images to the computer over the local network |
| ESP8266 NodeMCU V3, CH340 | Explicitly listed in the order | Independently control the LED strip, misting, pump, and buttons |
| 0.5 m, 30-LED RGB strip | Selected specification says WS2811, 12V; the title also mixes in WS2812 | Cloud weather lighting; verify physical voltage, DIN, chip, and grouping before applying power |
| STC89C52 learning kit | Screenshot shows an 8051 microcontroller kit | Buttons, wires, and similar parts may be reused after inspection; do not use its main board for now |
| Motor | Type and ratings not confirmed in the screenshot | Leave out for now; a servo could later move a sun-shaped element |

An ordinary motor cannot replace a water pump or misting module. Do not power a 12V strip from the development board or connect 12V to the board's 5V/3V3 pins.

## 2. Form and Structure

Suggested trial dimensions: base 200 mm wide × 180 mm deep, total height about 280 mm; cloud 160 mm wide × 100 mm deep × 80 mm high. Plant-pot diameter about 70–90 mm. These are appearance targets and should be adjusted after selecting the modules.

- A fixed rear support holds the cloud and routes wiring and drip tubing internally; no magnetic levitation.
- Divide the cloud into a removable top cover, a dry lighting chamber, and a separate waterproof misting box. Use a light-gray translucent shell with an internal diffuser.
- Mount a small reservoir for the matched misting assembly inside the cloud, initially reserving space for 30–50 mL; actual capacity depends on module dimensions. Remove the reservoir to refill it rather than pouring water into the whole device.
- Keep the misting assembly in its manufacturer's specified orientation and water level. Try a short outlet shroud to direct mist downward. Do not invert an ordinary humidifier to obtain downward mist.
- Put a removable plant pot, catch tray, and separate drip-irrigation reservoir in the base, initially reserving about 100–150 mL. Place the electronics compartment on the other side of a water barrier, not beneath a reservoir.
- Mount the LED strip on a heat-dissipating support in the dry area, away from absorbent cotton and standing water. Route catch-tray overflow away from electronics.
- Use side lighting beneath the cloud to make mist more visible. Mist is affected by airflow and buoyancy; it cannot be promised to fall vertically like raindrops.

Validate mist production with modules, plastic containers, and a simple support before fabricating the cloud shell. If a short shroud still causes substantial condensation or drifting, retain a localized mist effect beneath the cloud and use drip irrigation for actual watering.

## 3. System Roles

ESP32-CAM → local-network images → computer facial-expression program → local-network commands → ESP8266.

Buttons → ESP8266 → LED strip, misting module, drip pump.

A computer webcam can be used to debug the facial-expression program before switching to ESP32-CAM images. Computation runs on the computer; the camera board does not need to infer emotions. Initially limit recognition outputs to three facial cues: smiling, clearly frowning, and undetermined. Do not equate these cues with a person's actual psychological state. Process locally by default, do not save photos, and provide a camera-pause function.

The first ESP8266 version uses a custom nonblocking controller with sunny, cloudy, rainy, stop, and measured-watering commands. Lighting effects may use a strip-compatible library. WLED can be used for standalone strip testing, but the water system still needs separate control logic.

## 4. Weather Experience

| State | Lighting | Mist and water |
|---|---|---|
| Sunny | Warm white, gentle fade-in | No mist; do not water merely because someone looks happy |
| Cloudy | Dim cool white, revealing the light-gray shell | No mist |
| Rainy | Dim cool white with side lighting beneath the cloud | Initial trial: mist for 2 seconds, then pause for at least 60 seconds; adjust from measurements |
| Recovery | Slowly warm the light over about 20 seconds | Stop misting |
| Stop / low water | Gentle status indication | Turn off misting and pump |

RGB LEDs cannot emit gray light; use the light-gray shell, low brightness, and ambient lighting to create an overcast appearance. Physically test the appearance of white mixed by the existing RGB strip first.

Require facial cues to remain stable for about 3 seconds before changing state, and hold each state for at least 20 seconds. Return to quiet standby when no face is detected or confidence is low. Manual button input takes precedence over automatic recognition.

## 5. Two Independent Water Circuits

Circuit A: small reservoir inside the cloud → matched misting assembly → short outlet shroud → area around the plant. Include mist water in the plant's cumulative water intake. Disable further misting when soil is too wet, while retaining the rainy lighting effect.

Circuit B: base reservoir → miniature peristaltic pump → tubing inside the support → drip outlet above the soil. Do not immerse the outlet in soil or standing water; check whether dripping continues after the pump stops. Calibrate the peristaltic pump using measured flow. Wait and reassess after each watering event; do not repeatedly trigger watering from facial expressions.

Stage one uses only manually triggered measured watering. Collect water in a measuring cup first, calibrate mL/second, and connect it to the plant only after confirmation. Add soil-moisture sensing and a daily watering limit in stage two. Set the limit according to the plant, potting mix, and measured water consumption.

## 6. Additional Purchase List (Selection Criteria, Not Verified Product Orders)

| Item | Quantity | Selection requirements |
|---|---:|---|
| 5V misting assembly | 1 set | Matched misting disc, driver, and water-supply structure; documented continuous-enable control, preferably with low-water shutdown; avoid small USB humidifiers that can only cycle modes through a button |
| Low-water detection | 1 per reservoir | Float or level sensor matched to the reservoir; may be combined with reliable built-in misting protection |
| Miniature peristaltic pump | 1 | Documented rated voltage, current, and flow; include pump tubing, fittings, and drip outlet |
| 3.3V-compatible MOSFET driver module | As required by loads | Pump driver needs flyback protection; preferably control the misting module's EN rather than arbitrarily switching the piezoelectric-disc wiring |
| SN74AHCT125 level-shifter module | 1 | Convert 3.3V control signals to the strip's data input level; match the strip's actual data requirements |
| Regulated 12V adapter | 1 | Buy only after confirming the strip is 12V; size total power for the strip, pump, buck-converter losses, and startup current |
| 12V→5V DC-DC buck converter | 1 or separate branches | Allow margin above the maximum combined current of the camera, controller, and misting assembly; measure output after installation |
| Buttons, master switch, fuse, terminals, capacitors/resistors, wires | 1 batch | Size fuse and wires for the load; capacitor voltage ratings must exceed their supply rail; do not route high-current loads through a breadboard |
| Reservoirs, tubing, catch tray, support, and shell materials | 1 batch | Removable for cleaning, securely mounted, with serviceable openings |
| Capacitive soil-moisture probe | 1 in stage two | Documented output range; calibrate for the actual potting mix and keep electronics dry |
| ADS1115 ADC module | 1 in stage two | 3.3V supply and I²C connection to ESP8266; probe output must remain within the ADC's allowed range |

A0 input ranges differ among ESP8266 NodeMCU clones. Do not connect a moisture probe directly to A0 without checking. The external ADC above can avoid reliance on the board's voltage-divider configuration.

## 7. Power and Wiring Boundaries

After confirming the 12V strip, split the 12V supply into one strip branch and another branch stepped down for 5V loads. A 12V pump may use its own 12V branch; include a 5V pump in the 5V branch load instead. Logic and non-isolated drivers share ground.

- The controller supplies signals only. Do not drive a pump, LED strip, or misting assembly from GPIO or the board's regulator.
- Do not parallel external 5V and USB 5V without protection. Disconnect external board power when programming, or use a verified power-isolation arrangement.
- Pump and misting enables need a hardware-default-off state and must not activate during startup or reset. Avoid ESP8266 boot-strapping pins for critical load controls.
- No GPIO wiring table is specified yet: confirm the physical development board, strip pads, and misting interface first. Reserve I²C pins for stage two.
- A 12V strip may control three LEDs as one group. Thirty physical LEDs do not necessarily mean thirty addressable pixels. Confirm through inspection and a pixel-by-pixel test.

## 8. Build Sequence and Pass Criteria

1. Inventory and power-up: photograph the board model, strip pads, and motor label clearly; verify each supply rail with a multimeter. Test every load separately first.
2. Weather lighting: switch sunny/cloudy/rainy with buttons, starting at low brightness. Run continuously for 30 minutes without resets, flicker, or abnormal heat.
3. Standalone mist experiment: test 10 short mist cycles over a catch tray away from the computer. Record visibility, condensation locations, actual water consumption, drifting, and low-water shutdown. Define shell openings only after this passes.
4. Drip irrigation: calibrate flow in a measuring cup and repeat five times. Verify no continuous leakage after power-off and no automatic pumping after restart. Confirm the drip location and catch tray before connecting a plant.
5. Structural integration: install the cloud, support, and base; verify refilling, disassembly and cleaning, center of gravity, and wire routing. Repeat combined light, mist, and pump tests.
6. Computer integration: send commands manually first, then add facial-cue recognition. Manual switching must override recognition at any time.
7. Fault checks: shut down water circuits on network loss, camera disconnection, restart, and low water. Enforce local time limits on the controller rather than relying on a stop command from the computer. Network retries must not repeat the same watering command.

Estimated schedule: about 6–8 build sessions, each roughly half a day to a full day, depending on soldering experience, module arrivals, shell fabrication, and mist experiments. This is not a delivery commitment.

V0.1 acceptance: reliably demonstrate weather changes, real short-duration mist, manually triggered measured drip irrigation, computer facial-expression triggering, and manual stop. Add automatic plant care after sensor calibration; leave motor movement for a later version.

## 9. References

- Espressif official camera driver: https://github.com/espressif/esp32-camera
- Espressif CameraWebServer example: https://github.com/espressif/arduino-esp32/blob/master/libraries/ESP32/examples/Camera/CameraWebServer/CameraWebServer.ino
- WLED wiring and level-shifting guide: https://kno.wled.ge/basics/wiring-guides/
- DFRobot capacitive soil-moisture probe and calibration: https://wiki.dfrobot.com/sen0193/
