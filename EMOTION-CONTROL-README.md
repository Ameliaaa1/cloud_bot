# cloud_bot software prototype v2

## Startup

Before the first run on a new computer, install dependencies with `python -m pip install -r requirements.txt` and prepare the model weights as described below.

Double-click `start-cloud-bot.cmd` in the project. It switches to the correct directory and starts the computer webcam.
Connect the computer to the ESP32's cloud_bot hotspot. The repository default password is set-a-local-password; use the device's actual password if it has been changed.
The web address is http://192.168.4.1 . The web page and computer program share the same device state.

For the first upgrade, upload the entire `firmware/cloud_bot_existing_parts` sketch folder to the ESP32; app.js and web_app.h are both inside it.
Use `tools/upload-cloud-bot.ps1 -Port <actual-serial-port>`, or open the folder's ino file in Arduino IDE with AI Thinker ESP32-CAM selected.
Old firmware exposes only the weather field. The program explicitly requests an update; it cannot be used directly with the v2 client.

Keyboard: a selects automatic mode; s/c/r selects manual sunny/cloudy/rainy; q, Esc, or closing the window exits.
Clicking a weather state on the web page also selects manual mode. The ESP32 retains that state and the computer does not override it. Click the automatic-recognition control to resume automatic mode.
Expressions that trigger sunny or rainy use a default 25% confidence threshold. A candidate weather state must persist for at least 1.5 seconds before switching. Use `--smile-threshold` for the smile threshold and `--threshold` for other expressions. No face or a model error eventually returns the system to cloudy.
After the program exits or the connection drops, automatic mode returns to cloudy within 10 seconds; manual mode retains the user's selection.
Camera reads run in the background and retry after disconnection. If a Windows driver hangs inside its low-level read call, the main window can still exit, but recovering the driver may require unplugging/reconnecting the camera or restarting the program.

## Model

The model remains EmotiEffLib enet_b2_8, running the original graph directly through ONNX Runtime: 260×260 RGB input, ImageNet normalization, and eight-class softmax.
This avoids importing optional TensorFlow/Torch dependencies and bypasses the old environment's MessageFactory/GetPrototype error.
The maximum probability difference against the local EmotiEffLib 1.1.1 installation was approximately 1.49e-8 for the comparison input/output.
The existing weights are at `<user-home>/.emotiefflib/enet_b2_8.onnx`. On a new computer, obtain this model through the official EmotiEffLib project first; this repository does not redistribute the weights.
requirements.txt lists the main packages verified on the original computer. They were already installed there; reinstalling them or downgrading global protobuf was not necessary.
Expressions are interaction cues only. Accuracy needs to be observed under the user's actual lighting, distance, and expressions.

## Current outputs

Lighting and misting in this version are simulated states visible on the web page. LED-strip data, mister, and pump pins are not enabled.
Simulated rain-mode mist pulses last at most 300 ms, with at least 60 s between starts; leaving rainy mode stops them immediately. A physical water system still requires separately implemented low-water detection, driver circuitry, and experimentally validated limits.
The ESP32 camera preview and the computer's expression-recognition camera are separate. Images are not stored or uploaded to a remote service.

## Validation commands

```sh
python -m unittest discover -s tests -v
node tests/test_web.cjs
python emotion_control.py --check
```

The default device URL is http://192.168.4.1; override it with `--url`. Use `--camera 1` for the second camera or `--hold 3` to increase the hold time.
After editing app.js, run `python tools/embed-web.py` to embed it in web_app.h, then recompile and flash the firmware.

The documented version was flashed on COM6 and the device confirmed version=2 and camera=true. See SOFTWARE-VALIDATION.md for the validation record.
