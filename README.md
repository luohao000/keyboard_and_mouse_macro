# keyboard_and_mouse_macro

需要安装 pynput 库

`pip install pynput`

数据保存在 `.pkl` 文件中

## 如何使用

在命令行中输入 `py macro.py` 运行程序

按 `Enter` 开始录制，输入 `exit` 退出

输入文件名开始回放，例如 `test.pkl`

文件名后可以加参数，例如 `test.pkl 3 0.5 2.5`

参数依次表示重复次数，时间间隔，倍速

回放过程中可按 `Esc` 终止回放

### 可以在命令行中直接输入命令

如 `py macro.py test.pkl 3 0.5 2.5`
