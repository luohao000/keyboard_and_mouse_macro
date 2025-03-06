import ctypes
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

import sys
import msvcrt
import pickle
import time
from pynput import keyboard, mouse

# 存储键鼠数据
recorded_events = []
recording = True  # 标记是否继续记录

# 监听键盘事件
def on_key_press(key):
    key_str = get_key_string(key)
    recorded_events.append({
        "type": "key",
        "event": "press",
        "key": key_str,
        "time": time.time()
    })

def on_key_release(key):
    global recording
    key_str = get_key_string(key)
    recorded_events.append({
        "type": "key",
        "event": "release",
        "key": key_str,
        "time": time.time()
    })
    if key == keyboard.Key.esc:  # 按 ESC 停止监听
        recording = False
        return False

# 处理普通按键 & 特殊按键
def get_key_string(key):
    try:
        return key.char  # 处理普通按键（a, b, c, 1, 2, 3）
    except AttributeError:
        return str(key)  # 处理特殊按键（Ctrl, Shift, Enter 等）

# 监听鼠标事件
def on_click(x, y, button, pressed):
    recorded_events.append({
        "type": "mouse",
        "event": "press" if pressed else "release",
        "button": str(button),
        "x": x,
        "y": y,
        "time": time.time()
    })

def on_move(x, y):
    recorded_events.append({
        "type": "mouse",
        "event": "move",
        "x": x,
        "y": y,
        "time": time.time()
    })

# 监听鼠标滚轮事件
def on_scroll(x, y, dx, dy):
    recorded_events.append({
        "type": "mouse",
        "event": "scroll",
        "x": x,
        "y": y,
        "dx": dx,  # 水平滚动量
        "dy": dy,  # 垂直滚动量
        "time": time.time()
    })

# **启动监听线程**
def start_listeners():
    global recorded_events
    recorded_events = []  # 清空旧数据
    print("开始录制...（请按 ESC 停止录制）")
    global recording
    with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as k_listener, mouse.Listener(on_click=on_click, on_move=on_move, on_scroll=on_scroll) as m_listener:
        k_listener.join()  # 等待 ESC 退出
        m_listener.stop()  # 停止鼠标监听
    # **保存数据到 pickle**
    with open("temp_data.pkl", "wb") as f:
        pickle.dump(recorded_events, f)
    print("录制完成，文件已保存为 temp_data.pkl")

# **回放键鼠事件**
def replay_events(str, x):
    try:
        with open(str, "rb") as f:
            events = pickle.load(f)
    except FileNotFoundError:
        print("没有找到文件")
        return
    except Exception as e:
        print(f"读取文件出错: {e}")
        return
    mouse_controller = mouse.Controller()
    keyboard_controller = keyboard.Controller()
    start_time = events[0]["time"]
    for event in events:
        time.sleep((event["time"] - start_time) / x)  # 保持时间间隔
        start_time = event["time"]
        if event["type"] == "key":
            key = event["key"]
            key_to_press = get_key_from_string(key)  # 转换为可按的键
            if event["event"] == "press":
                keyboard_controller.press(key_to_press)
            elif event["event"] == "release":
                keyboard_controller.release(key_to_press)
        elif event["type"] == "mouse":
            if event["event"] == "move":
                mouse_controller.position = (event["x"], event["y"])
            elif event["event"] == "press":
                mouse_controller.press(mouse.Button[event["button"].split(".")[-1]])
            elif event["event"] == "release":
                mouse_controller.release(mouse.Button[event["button"].split(".")[-1]])
            elif event["event"] == "scroll":
                mouse_controller.scroll(event["dx"], event["dy"])  # 回放滚轮操作
    print("回放完成")

# 字符串转换为 pynput 可识别的按键对象
def get_key_from_string(key_str):
    if key_str.startswith("Key."):
        return getattr(keyboard.Key, key_str[4:])
    return key_str

def clear_input_buffer():
    """清空标准输入缓冲区（Windows 专用）"""
    while msvcrt.kbhit():  # 检查是否有未处理的按键
        msvcrt.getch()     # 读取并丢弃这些按键

def main():
    print("按 Enter 开始录制，输入 exit 退出")
    print("输入文件名开始回放，例如 test.pkl")
    print("文件名后可以加参数，例如 test.pkl 3 0.5 2.5")
    print("参数依次表示重复次数，时间间隔，倍速")
    _exit = False
    while True:
        clear_input_buffer()
        if len(sys.argv) > 1:
            command = " ".join(sys.argv[1:])
            _exit = True
        else:
            command = input("请输入命令: ")
        if command == "":
            start_listeners()
        elif command.lower() == "exit":
            print("退出程序")
            break
        else:
            a = command.split()
            c = len(a)
            if c == 1:
                print("开始回放...")
                replay_events(command, 1)
            elif c > 1:
                n = int(a[1])
                t = float(a[2]) if c > 2 else 0 # 时间间隔
                x = float(a[3]) if c > 3 else 1 # 倍速
                for i in range(1, n + 1):
                    print("开始第 " + str(i) + " 次回放")
                    replay_events(a[0], x)
                    if i < n:
                        time.sleep(t)
            if _exit == True:
                break

if __name__ == "__main__":
    main()
