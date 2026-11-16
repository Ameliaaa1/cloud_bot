# Software prototype v2 validation record

2026-11-12

- Python: nine logic/device-client tests passed.
- Web: six behavior checks passed (state rendering, manual requests, return to automatic mode, disconnection, recovery, and old-firmware notification). The web-script syntax check passed, and the embedded header matched the source file.
- Model: the locally cached enet_b2_8 ONNX model ran successfully. Against EmotiEffLib 1.1.1, the maximum probability difference for fixed random input was 1.49e-8. The new program loads ONNX directly without triggering the TensorFlow GetPrototype error.
- Firmware: compilation passed for AI Thinker ESP32-CAM / Espressif core 3.3.12; program size was approximately 1,032,821 bytes, with 59,368 bytes of static memory.
- Flashing: the ESP32 was identified on COM6, the upload succeeded, and programmer verification passed.
- Physical-device serial query: {"version":2,"weather":"cloudy","control":"auto","camera":true,"auto_online":false,"outputs":{"hardware_enabled":false,"light":"cloudy","mist_simulated":false}}

2026-11-13: physical-device HTTP acceptance checks were completed after connecting to cloud_bot. The device returned the web page, browser script, and ESP32 camera JPEG successfully. The HTTP endpoints used by the web page confirmed the sunny, cloudy, and rainy manual states. Automatic signals did not override a manual selection, and returning to automatic mode applied the latest suggestion. After automatic signals stopped, the device returned to cloudy after approximately 10 seconds.

The computer webcam captured 640×480 images successfully. After the recognition window was launched with start-cloud-bot.cmd, the ESP32 received automatic states sent by the program. During observation, the device remained in automatic cloudy mode and samples did not detect a face. Weather switching triggered by real-person expressions and recognition accuracy remain pending validation. LED-strip and mist outputs are still simulated.

This is a runnable software prototype. Physical outputs remain disabled until the drivers and water system are ready for integration testing.
