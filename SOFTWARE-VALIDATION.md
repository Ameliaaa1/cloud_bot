# 软件原型 v2 验证记录

2026-11-12

- Python：9 项逻辑/设备客户端测试通过。
- 网页：6 项行为检查通过（状态渲染、手动请求、恢复自动、断线、恢复、旧固件提示）。网页脚本语法检查通过，嵌入头文件与源文件一致。
- 模型：本地缓存 enet_b2_8 ONNX 运行成功；对照 EmotiEffLib 1.1.1，固定随机输入的最大概率差 1.49e-8。新程序直接加载 ONNX，不触发 TensorFlow GetPrototype 报错。
- 固件：AI Thinker ESP32-CAM / Espressif core 3.3.12 编译通过，程序约 1,032,821 bytes，静态内存 59,368 bytes。
- 烧录：COM6 上确认 ESP32 后上传成功，烧录器校验通过。
- 实机串口查询：{"version":2,"weather":"cloudy","control":"auto","camera":true,"auto_online":false,"outputs":{"hardware_enabled":false,"light":"cloudy","mist_simulated":false}}

2026-11-13 连接 cloud_bot 后完成实机 HTTP 验收。设备成功返回网页、浏览器脚本和 ESP32 摄像头 JPEG。通过网页使用的 HTTP 接口确认晴、阴、雨三种手动状态，自动信号不会覆盖手动选择，恢复自动后会采用最新建议。停止发送自动信号后，设备约 10 秒回到阴天。

电脑摄像头成功取得 640×480 画面。通过 start-cloud-bot.cmd 启动识别窗口后，ESP32 收到程序发送的自动状态。观察期间设备保持自动阴天，采样未检测到人脸，真人表情触发天气切换和识别准确率仍待验证。灯带和喷雾仍为模拟输出。

这是一版可运行的软件原型。实际实体输出保持关闭，待驱动和水路到位再联调。
