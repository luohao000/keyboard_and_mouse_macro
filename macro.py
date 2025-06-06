import ctypes
PROCESS_PER_MONITOR_DPI_AWARE = 2
ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)

import sys
import msvcrt
import json
import time
from pynput import keyboard, mouse
from pynput.keyboard import KeyCode

# 存储键鼠数据
recorded_events = []

# 监听键盘事件
def on_key_press(key):
    if key == keyboard.Key.esc:
        return False
    recorded_events.append({
        "type": "key",
        "event": "press",
        "key": str(key),
        "time": time.time()
    })

def on_key_release(key):
    recorded_events.append({
        "type": "key",
        "event": "release",
        "key": str(key),
        "time": time.time()
    })

def on_esc_press(key):
    if key == keyboard.Key.esc:
        return False

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
    with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as k_listener, mouse.Listener(on_click=on_click, on_move=on_move, on_scroll=on_scroll) as m_listener:
        k_listener.join()  # 等待 ESC 退出
        m_listener.stop()  # 停止鼠标监听
    with open("temp.json", "w") as f:
        json.dump(recorded_events, f, indent=4)
    print("录制完成，文件已保存为 temp.json")

# **回放键鼠事件**
def replay_events(str, x):
    try:
        with open(str, "r", encoding='utf-8') as f:
            events = json.load(f)
    except FileNotFoundError:
        print("没有找到文件")
        return
    except Exception as e:
        print(f"读取文件出错: {e}")
        return
    mouse_controller = mouse.Controller()
    keyboard_controller = keyboard.Controller()
    listener = keyboard.Listener(on_press = on_esc_press)
    listener.start()
    start_time = events[0]["time"]
    for event in events:
        if not listener.is_alive():
            print("回放停止")
            return True
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
    listener.stop()
    print("回放完成")


# 字符串转换为 pynput 可识别的按键对象
def get_key_from_string(key_str):
    if key_str.startswith("Key."):
        return getattr(keyboard.Key, key_str[4:])
    elif key_str.startswith("'") and key_str.endswith("'"):
        return key_str[1:-1]
    elif key_str.startswith('<') and key_str.endswith('>'):
        return KeyCode(vk = int(key_str[1:-1]))

def clear_input_buffer():
    """清空标准输入缓冲区（Windows 专用）"""
    while msvcrt.kbhit():  # 检查是否有未处理的按键
        msvcrt.getch()     # 读取并丢弃这些按键

def interruptible_sleep(seconds):
    """可中断的睡眠函数，支持 ESC 键中断"""
    if seconds <= 0:
        return True
    
    esc_pressed = [False]

    def stop_handler(key):
        if key == keyboard.Key.esc:
            esc_pressed[0] = True
            return False
    
    listener = keyboard.Listener(on_press=stop_handler)
    listener.start()
    
    start_time = time.time()
    while time.time() - start_time < seconds:
        if esc_pressed[0]:  # 检查是否按下了 ESC
            break
        time.sleep(0.1)  # 每次最多睡眠 0.1 秒
    
    listener.stop()
    return not esc_pressed[0]  # 返回 True 表示正常完成，False 表示被中断

def main():
    if len(sys.argv) == 1:
        print("按 Enter 开始录制，输入 exit 退出")
        print("输入文件名开始回放，例如 temp.json")
        print("文件名后可以加参数，例如 temp.json 3 0.5 2.5")
        print("参数依次表示重复次数，时间间隔，倍速")
        print("回放过程中可按 Esc 终止回放")
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
                    b = replay_events(a[0], x)
                    if b == True: # 回放被中断
                        break
                    if i < n and t > 0:
                        print(f"等待 {t} 秒后开始下一次回放")
                        if not interruptible_sleep(t):
                            print("回放停止")
                            break
            if _exit == True:
                break

if __name__ == "__main__":
    main()
