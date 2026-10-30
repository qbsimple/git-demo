from maix import camera, display, image, touchscreen, app, time, nn, uart, gpio, pinmap
import os, math, struct
import sys

# 添加串口协议路径
sys.path.append('/root/exam')
import serial_protocol

# ---------- 0. 参数 ----------
THRESH = 4
STABLE_N = 2
THRESHOLD_FILE = "/mnt/data/my_thresholds.txt"

# 读取阈值参数
try:
    with open(THRESHOLD_FILE, "r") as f:
        for ln in f:
            ln = ln.strip()
            if ln.startswith("thresh:"):
                THRESH = int(ln.split(":")[1])
            elif ln.startswith("stable:"):
                STABLE_N = int(ln.split(":")[1])
except Exception:
    pass

# ---------- 模型 ----------
detector = nn.YOLO11(model="/root/models/my_model5/yolo11n_int8.mud", dual_buff=True)  # YOLO11S

labels = ["hu","kongque","lang","hou","xiang"]
CLS_NUM = len(labels)
CLS_COLORS = [
    image.COLOR_RED,
    image.COLOR_BLUE,
    image.COLOR_GREEN,
    image.COLOR_YELLOW,
    image.Color.from_rgb(255, 165, 0)
]
DECAY = 0.5

# ---------- 硬件 ----------
disp = display.Display()
cam = camera.Camera(240, 240, fps=60)
disp.set_backlight(40)
cam.awb_mode(0)
cam.exp_mode(0)
cam.luma(40)
cam.constrast(50)
cam.saturation(50)
cam.skip_frames(30)

# 串口配置
comm_proto = serial_protocol.SerialProtocol()
device = "/dev/ttyS0"
serial = uart.UART(device, 500000)
data_buffer = bytes()

# GPIO配置
pinmap.set_pin_function("B3", "GPIOB3")
led = gpio.GPIO("GPIOB3", gpio.Mode.OUT)
led.value(0)
pinmap.set_pin_function("A18", "GPIOA18")
led1 = gpio.GPIO("GPIOA18", gpio.Mode.OUT)
led1.value(1)
# 触摸屏
ts = touchscreen.TouchScreen()
_image_width = 240
_image_height = 240
_btn_width = _image_width // 4
_btn_height = _image_height // 7
last_touch_read_time = time.ticks_ms()
x = y = 0
pressed = False
torch_flag = False
torch_success = False

# 按钮定义
exit_label = "<Exit"
exit_btn_pos = [0, 0, _btn_width, _btn_height]

thr_val_label = f"T{THRESH}"
thr_val_btn_pos = [0*_btn_width, 5*_btn_height, _btn_width, _btn_height]

stable_val_label = f"S{STABLE_N}"
stable_val_btn_pos = [1*_btn_width, 5*_btn_height, _btn_width, _btn_height]

# ---------- 计数器 ----------
cnt = [0] * CLS_NUM
stable_cnt = [0] * CLS_NUM
stable_ok = [False] * CLS_NUM

# ---------- 工具函数 ----------
def save_thresholds():
    with open(THRESHOLD_FILE, "w") as file:
        file.write(f"thresh: {THRESH}\n")
        file.write(f"stable: {STABLE_N}\n")

def is_in_button(x, y, btn_pos):
    return x > btn_pos[0] and x < btn_pos[0] + btn_pos[2] and y > btn_pos[1] and y < btn_pos[1] + btn_pos[3]

def process_serial_data():
    global data_buffer, serial
    length = serial.available()
    if length > 0:
        data = serial.read(length)
        data_buffer += data
        
        while True:
            rc, bytes_redundant = comm_proto.is_valid(data_buffer)
            
            if bytes_redundant > 0:
                data_buffer = data_buffer[bytes_redundant:]
            
            if rc >= 0:
                result = comm_proto.decode(data_buffer)
                if len(result) == 24:
                    qr_id, cnt10,cnt20, cnt30, cnt40, cnt50 = struct.unpack('<iiiiii', result)
                    print(f'接收数据: qr_id={qr_id},cnt10={cnt10}, cnt20={cnt20}, cnt30={cnt30},cnt40={cnt40},cnt50={cnt50}')
                                  
                packet_len = comm_proto.length(data_buffer)
                if packet_len > 0:
                    data_buffer = data_buffer[packet_len:]
                else:
                    break
            else:
                break

def send_serial_data(cls_id, center_x, center_y, cnt1, cnt2, cnt3, cnt4, cnt5):
    payload = struct.pack('<iiiiiiii', cls_id, center_x, center_y, cnt1, cnt2, cnt3, cnt4, cnt5)
    encoded = comm_proto.encode(payload)
    serial.write(encoded)

while not app.need_exit():
    # 1. 处理串口数据
    process_serial_data()

    img = cam.read()
    
    # 直接使用完整图像进行检测
    objs = detector.detect(img, conf_th=0.55, iou_th=0.5)

    # 2.1 当前帧每类个数
    curr_num = [0] * CLS_NUM
    centers = [None] * CLS_NUM
    for obj in objs:
        if 0 <= obj.class_id < CLS_NUM:
            curr_num[obj.class_id] += 1
            # 计算中心点
            cx = obj.x + obj.w // 2
            cy = obj.y + obj.h // 2
            centers[obj.class_id] = (cx, cy)
            
            # 绘制检测框和中心点
            color = CLS_COLORS[obj.class_id % CLS_NUM]
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=color)
            img.draw_string(obj.x, obj.y,
                          f'{labels[obj.class_id]}:{obj.score:.2f}',
                          color=color)
            img.draw_circle(cx, cy, 3, color=color)

    # 2.2 更新平滑计数器
    for i in range(CLS_NUM):
        if curr_num[i]:
            cnt[i] += curr_num[i]
        else:
            cnt[i] *= DECAY
        cnt[i] = int(min(cnt[i], 300))

        # 5帧二次确认
        if cnt[i] >= THRESH and not stable_ok[i]:
            stable_cnt[i] += 1
            if stable_cnt[i] >= STABLE_N:
                stable_ok[i] = True
        else:
            stable_cnt[i] = 0

    # 发送数据（放在检测循环外，避免重复发送）
    if len(objs) > 0:
        # 取第一个检测到的物体（或按需修改逻辑）
        obj = objs[0]
        cx = obj.x + obj.w // 2
        cy = obj.y + obj.h // 2
        
        # 发送5个类别的计数（cnt[0]~cnt[4]）
        send_serial_data(
            obj.class_id + 1,  # 类别ID（+1避免0值）
            cx,               # 中心x坐标
            cy,               # 中心y坐标
            curr_num[0],    # cnt1: 类别0计数
            curr_num[1],    # cnt2: 类别1计数
            curr_num[2],    # cnt3: 类别2计数
            curr_num[3],    # cnt4: 类别3计数
            curr_num[4] if CLS_NUM > 4 else 0  # cnt5: 类别4计数（如果存在）
        )
    else:
        # 没有识别到物体时发送666
        send_serial_data(
            666,    # 类别ID设为0表示无效
            666,  # 中心x坐标设为666
            666,  # 中心y坐标设为666
            666,  # cnt1设为666
            666,  # cnt2设为666
            666,  # cnt3设为666
            666,  # cnt4设为666
            666   # cnt5设为666
        )

    # 显示类别数量
    y0 = 25
    for cls in range(CLS_NUM):
        disp_num = curr_num[cls] if stable_ok[cls] else 0
        img.draw_string(150, y0, f'{labels[cls]}:{disp_num}', CLS_COLORS[cls], scale=1)
        y0 += 15

    # 触摸处理
    current_time = time.ticks_ms()
    if current_time - last_touch_read_time >= 50:
        last_touch_read_time = current_time
        x, y, pressed = ts.read()
        x, y = image.resize_map_pos_reverse(img.width(), img.height(), disp.width(), disp.height(), image.Fit.FIT_CONTAIN, x, y)
        if torch_flag == False and pressed:
            torch_flag = True
            torch_success = False
        if pressed == False and torch_flag:
            torch_flag = False
            torch_success = True
    img.draw_circle(x, y, 1, image.Color.from_rgb(255, 255, 255), 2)

    # 按钮处理
    # Exit按钮
    img.draw_string(8, 12, exit_label, image.Color.from_rgb(255, 0, 255))
    img.draw_rect(exit_btn_pos[0], exit_btn_pos[1], exit_btn_pos[2], exit_btn_pos[3], image.Color.from_rgb(255, 0, 255), 2)
    if torch_success and is_in_button(x, y, exit_btn_pos):
        torch_success = False
        app.set_exit_flag(True)

    # T按钮
    img.draw_rect(thr_val_btn_pos[0], thr_val_btn_pos[1], thr_val_btn_pos[2], thr_val_btn_pos[3], image.Color.from_rgb(255,0,255), 2)
    img.draw_string(thr_val_btn_pos[0]+5, thr_val_btn_pos[1]+5, f"T{THRESH}", image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, thr_val_btn_pos):
        torch_success = False
        THRESH = THRESH % 10 + 1
        save_thresholds()

    # S按钮
    img.draw_rect(stable_val_btn_pos[0], stable_val_btn_pos[1], stable_val_btn_pos[2], stable_val_btn_pos[3], image.Color.from_rgb(255,0,255), 2)
    img.draw_string(stable_val_btn_pos[0]+5, stable_val_btn_pos[1]+5, f"S{STABLE_N}", image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, stable_val_btn_pos):
        torch_success = False
        STABLE_N = STABLE_N % 10 + 1
        save_thresholds()

    # 显示FPS
    fps = time.fps()
    img.draw_string(160, 10, f"FPS{fps:.1f}", image.Color.from_rgb(255, 255, 0), scale=1)
    disp.show(img)

# 资源释放
cam.close()
disp.close()
serial.close()
print("程序结束，资源已释放")