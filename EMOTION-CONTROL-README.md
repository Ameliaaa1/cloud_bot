# cloud_bot 第二阶段：表情联动

这一版默认使用开源 EmotiEffLib 的 EfficientNet-B2 AffectNet ONNX 模型，再把天气状态发给 ESP32-CAM。它是一个互动原型，不是心理状态诊断。图像只在本机处理，不保存或上传。

## 使用

1. 让 ESP32-CAM 通电，并让运行程序的电脑连接 Wi‑Fi `cloud_bot`，密码 `set-a-local-password`。同一台电脑不能同时保持其他 Wi‑Fi 网络作为主要连接；如果系统提示无互联网，选择保持连接。
2. 关闭 Arduino IDE 的串口监视器，避免占用 COM5。网页可以关闭，也可以保留。
3. 在 PowerShell 中进入本项目目录，运行：

   ```powershell
   python .\emotion_control.py
   ```

4. 程序会打开摄像头窗口。`Happiness`/`Surprise` 会切换晴天，`Sadness`/`Anger`/`Fear`/`Disgust` 会切换雨天，其余状态为阴天。程序会显示情绪标签和置信度，并做短时稳定处理。第一次运行会从 EmotiEffLib 官方仓库下载 `enet_b2_8.onnx` 模型文件，需要等待。
5. 键盘控制：`a` 自动、`s` 晴天、`c` 阴天、`r` 雨天、`q` 或 `Esc` 退出。

如果不是默认摄像头，可用：

```powershell
python .\emotion_control.py --camera 1
```

如需对比旧版传统微笑检测：

```powershell
python .\emotion_control.py --engine haar
```

如果 ESP32 地址改变，可用：

```powershell
python .\emotion_control.py --url http://192.168.4.1
```

## 当前限制

- “开心”只用微笑检测作演示线索；它不判断真实情绪，也不保存或上传图像。
- 这一版控制的是网页天气状态。下一阶段把同一个 `mode` 接到灯带控制器，再接雾化与滴灌。
- 电脑必须连接 ESP32 热点才能发送 HTTP；手机连接热点时，电脑不能同时发送。


