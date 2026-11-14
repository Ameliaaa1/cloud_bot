# cloud_bot 软件原型 v2

## 启动

首次在新电脑上运行时，先用 `python -m pip install -r requirements.txt` 安装依赖，并按下方说明准备模型权重。

双击项目中的 `start-cloud-bot.cmd`。它会自动进入正确目录，再启动电脑摄像头。
电脑连接 ESP32 的 cloud_bot 热点；仓库默认密码 set-a-local-password，设备若改过则以实际密码为准。
网页地址：http://192.168.4.1 。网页和电脑程序使用同一个设备状态。

首次升级需把 `firmware/cloud_bot_existing_parts` 整个文件夹上传到 ESP32；app.js 与 web_app.h 都在其中。
使用 tools/upload-cloud-bot.ps1 -Port 实际串口，或 Arduino IDE 打开该文件夹的 ino，板型 AI Thinker ESP32-CAM。
旧版固件只有 weather 字段，程序会明确提示更新，不能直接使用 v2 客户端。

键盘：a 切自动；s/c/r 手动晴/阴/雨；q、Esc 或关闭窗口退出。
网页点击天气也会切手动；手动状态由 ESP32 保持，电脑不会覆盖。点击自动识别恢复。
触发晴天或雨天的表情默认使用 25% 置信度门槛。同一候选天气持续至少 1.5 秒才切换。可用 `--smile-threshold` 调整微笑门槛，用 `--threshold` 调整其他表情门槛。无脸或模型异常最终回到阴天。
退出程序或断线后，设备自动模式最多 10 秒回到阴天；手动模式保留用户选择。
摄像头读取放在后台，掉线后重试；如果 Windows 驱动卡死在底层 read，主界面仍可退出，但需重新插拔摄像头或重启程序以恢复该驱动。

## 模型

模型仍为 EmotiEffLib enet_b2_8，使用 ONNX Runtime 直接执行原始图，260×260 RGB 输入、ImageNet 归一化、8 类 softmax。
这样不再导入可选 TensorFlow/Torch，避开旧环境的 MessageFactory/GetPrototype 报错。
与本机 EmotiEffLib 1.1.1 的对照输入输出最大概率差约 1.49e-8。
现有权重位置：用户目录/.emotiefflib/enet_b2_8.onnx。首次换电脑需先通过官方 EmotiEffLib 获取该模型；不随本项目重新分发权重。
requirements.txt 列出此电脑验证过的主要包。当前电脑已经安装，无需重复安装或降级全局 protobuf。
表情只代表互动线索，准确率需要在用户实际光照、距离和表情下观察。

## 当前输出

本版灯效与喷雾为模拟状态，网页可查看。没有启用灯带数据引脚、雾化器或水泵引脚。
雨天模拟喷雾脉冲最长 300 ms，相邻启动至少间隔 60 s；离开雨天立即停止。实体水路完成后仍需单独实现缺水检测、驱动电路和实测限量。
ESP32 镜头网页预览与电脑表情摄像头分开，不保存照片，不上传图像。

## 验证命令

python -m unittest discover -s tests -v
node tests/test_web.cjs
python emotion_control.py --check

默认访问 http://192.168.4.1，也可加 --url；--camera 1 选择第二个摄像头；--hold 3 增加持续时间。
app.js 修改后运行 python tools/embed-web.py，把代码嵌入 web_app.h，再重新编译上传固件。

本次已烧录到 COM6，设备确认 version=2、camera=true。验证记录见 SOFTWARE-VALIDATION.md。
