from maix import camera, display, image, touchscreen, app, time, nn, uart, gpio, pinmap
import os, math, struct
import sys

# 添加串口协议路径
sys.path.append('/root/exam')
import serial_protocol

# ---------- 0. 参数 ----------
THRESH = 4
STABLE_N = 2

# 读取配置文件
THRESHOLD_FILE = "/mnt/data/my_thresholds.txt"
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

# ---------- 1. 模型 ----------
detector = nn.YOLO11(model="/root/models/my_model3/yolo11s_int8.mud", dual_buff=True)
labels = ["kongque", "lang", "hou", "hu"]
CLS_NUM = len(labels)
CLS_COLORS = [image.COLOR_RED, image.COLOR_BLUE, image.COLOR_GREEN, image.COLOR_YELLOW]
DECAY = 0.5

# 摄像头配置
disp = display.Display()
cam = camera.Camera(320, 240, fps=60)
disp.set_backlight(40)
cam.luma(40)
cam.constrast(50)
cam.saturation(50)
cam.skip_frames(30)

# 串口通信配置
comm_proto = serial_protocol.SerialProtocol()
device = "/dev/ttyS0"
serial = uart.UART(device, 500000)
data_buffer = bytes()

# GPIO配置
pinmap.set_pin_function("B3", "GPIOB3")
led = gpio.GPIO("GPIOB3", gpio.Mode.OUT)
led.value(0)

# 触摸屏配置
ts = touchscreen.TouchScreen() 
torch_flag = False
torch_success = False
_image_width = 320
_image_height = 240
_btn_width = _image_width // 6
_btn_height = _image_height // 7

last_touch_read_time = time.ticks_ms()
x = 0
y = 0
pressed = False

# 按钮定义
exit_label = "<Exit"
exit_btn_pos = [0, 0, _btn_width, _btn_height]
thr_val_label = f"T{THRESH}"
thr_val_btn_pos = [0*_btn_width, 5*_btn_height, _btn_width, _btn_height]
stable_val_label = f"S{STABLE_N}"
stable_val_btn_pos = [1*_btn_width, 5*_btn_height, _btn_width, _btn_height]

# 平滑计数
cnt = [0] * CLS_NUM
stable_cnt = [0] * CLS_NUM
stable_ok = [False] * CLS_NUM

# 区域标记
cut_id_x = [0]*8   # 1-7有效
cut_id_y = [0]*10  # 1-9有效

def save_thresholds():
    with open(THRESHOLD_FILE, "w") as file:
        file.write(f"thresh: {THRESH}\n")
        file.write(f"stable: {STABLE_N}\n")

def is_in_button(x, y, btn_pos):
    return x > btn_pos[0] and x < btn_pos[0] + btn_pos[2] and y > btn_pos[1] and y < btn_pos[1] + btn_pos[3]

def process_serial_data():
    global data_buffer, serial, liadar_x_cm, liadar_y_cm
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
                if len(result) == 32:
                    qr_id, liadar_x_cm, liadar_y_cm, to_stm32, color, light, buzzle, change_start = struct.unpack('<iiiiiiii', result)
                    print(f'接收数据: qr_id={qr_id},liadar_x_cm={liadar_x_cm}, liadar_y_cm={liadar_y_cm}')
                                 
                packet_len = comm_proto.length(data_buffer)
                if packet_len > 0:
                    data_buffer = data_buffer[packet_len:]
                else:
                    break
            else:
                break

def send_serial_data(cls_id, center_x, center_y):
    # 修改为与第二个版本相同的发送格式
    payload = struct.pack('<iii', cls_id, center_x, center_y)
    encoded = comm_proto.encode(payload)
    serial.write(encoded)

def get_region_index():
    global liadar_x_cm, liadar_y_cm
    idx_x = 0
    idx_y = 0
    
    if -15 < liadar_x_cm <= 15:           idx_x = 1
    elif 35 < liadar_x_cm <= 65:          idx_x = 2
    elif 85 < liadar_x_cm <= 115:         idx_x = 3
    elif 135 < liadar_x_cm <= 165:        idx_x = 4
    elif 185 < liadar_x_cm <= 215:        idx_x = 5
    elif 235 < liadar_x_cm <= 265:        idx_x = 6
    elif 285 < liadar_x_cm <= 315:        idx_x = 7

    if -15 < liadar_y_cm <= 15:           idx_y = 9
    elif 35 < liadar_y_cm <= 65:          idx_y = 8
    elif 85 < liadar_y_cm <= 115:         idx_y = 7
    elif 135 < liadar_y_cm <= 165:        idx_y = 6
    elif 185 < liadar_y_cm <= 215:        idx_y = 5
    elif 235 < liadar_y_cm <= 265:        idx_y = 4
    elif 285 < liadar_y_cm <= 315:        idx_y = 3
    elif 335 < liadar_y_cm <= 365:        idx_y = 2
    elif 385 < liadar_y_cm <= 415:        idx_y = 1

    return idx_x, idx_y

while not app.need_exit():
    # 初始化变量
    curr_num = [0] * CLS_NUM
    centers = [None] * CLS_NUM
    
    # 1. 处理串口数据
    process_serial_data()

    # 2. 获取当前区域索引
    idx_x, idx_y = 0, 0
    if 'liadar_x_cm' in globals() and 'liadar_y_cm' in globals():
        idx_x, idx_y = get_region_index()

    # 3. 检查区域是否已检测
    region_checked = True
    if idx_x > 0 and cut_id_x[idx_x] == 1:
        region_checked = True
    if idx_y > 0 and cut_id_y[idx_y] == 1:
        region_checked = True

    # 读取摄像头图像
    img = cam.read()
    
    if not region_checked:
        # 区域未检测，进行物体检测
        objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
        
        for obj in objs:
            if 0 <= obj.class_id < CLS_NUM:
                curr_num[obj.class_id] += 1
                cx = obj.x + obj.w // 2
                cy = obj.y + obj.h // 2
                centers[obj.class_id] = (cx, cy)
                
                color = CLS_COLORS[obj.class_id % CLS_NUM]
                img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=color)
                img.draw_string(obj.x, obj.y, f'{labels[obj.class_id]}:{obj.score:.2f}', color=color)
                img.draw_circle(cx, cy, 3, color=color)
                
                # 修改发送函数调用，去掉stable_cnt参数
                send_serial_data(obj.class_id + 1, cx, cy)

        # 检测到物体则标记区域
        if len(objs) > 0:
            if idx_x > 0:
                cut_id_x[idx_x] = 1
            if idx_y > 0:
                cut_id_y[idx_y] = 1
    else:
        # 区域已检测，显示提示信息
        img.draw_string(100, 100, "1", color=image.COLOR_WHITE)

    # 4. 更新平滑计数器
    for i in range(CLS_NUM):
        if curr_num[i]:
            cnt[i] += curr_num[i]
        else:
            cnt[i] *= DECAY
        cnt[i] = int(min(cnt[i], 300))

        if cnt[i] >= THRESH and not stable_ok[i]:
            stable_cnt[i] += 1
            if stable_cnt[i] >= STABLE_N:
                stable_ok[i] = True
        else:
            stable_cnt[i] = 0

    # 5. 显示检测结果
    y0 = 25
    for cls in range(CLS_NUM):
        disp_num = curr_num[cls] if stable_ok[cls] else 0
        img.draw_string(225, y0, f'{labels[cls]}:{disp_num}', CLS_COLORS[cls], scale=1)
        y0 += 18

    # 6. 处理触摸事件
    current_time = time.ticks_ms()
    if current_time - last_touch_read_time >= 50:
        last_touch_read_time = current_time
        x, y, pressed = ts.read()
        x, y = image.resize_map_pos_reverse(img.width(), img.height(), disp.width(), disp.height(), image.Fit.FIT_CONTAIN, x, y)
        
        if not torch_flag and pressed:
            torch_flag = True
            torch_success = False
        if not pressed and torch_flag:
            torch_flag = False  
            torch_success = True
    
    img.draw_circle(x, y, 1, image.Color.from_rgb(255, 255, 255), 2)

    # 7. 绘制按钮和处理按钮事件
    # 退出按钮
    img.draw_string(8, 12, exit_label, image.Color.from_rgb(255, 0, 255))
    img.draw_rect(exit_btn_pos[0], exit_btn_pos[1], exit_btn_pos[2], exit_btn_pos[3], image.Color.from_rgb(255, 0, 255), 2)
    if torch_success and is_in_button(x, y, exit_btn_pos):
        torch_success = False
        app.set_exit_flag(True)

    # THRESH按钮
    img.draw_rect(thr_val_btn_pos[0], thr_val_btn_pos[1], thr_val_btn_pos[2], thr_val_btn_pos[3], image.Color.from_rgb(255,0,255), 2)
    img.draw_string(thr_val_btn_pos[0]+5, thr_val_btn_pos[1]+5, f"T{THRESH}", image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, thr_val_btn_pos):
        torch_success = False
        THRESH = THRESH % 10 + 1
        save_thresholds()

    # STABLE_N按钮
    img.draw_rect(stable_val_btn_pos[0], stable_val_btn_pos[1], stable_val_btn_pos[2], stable_val_btn_pos[3], image.Color.from_rgb(255,0,255), 2)
    img.draw_string(stable_val_btn_pos[0]+5, stable_val_btn_pos[1]+5, f"S{STABLE_N}", image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, stable_val_btn_pos):
        torch_success = False
        STABLE_N = STABLE_N % 10 + 1
        save_thresholds()

    # 8. 显示FPS
    fps = time.fps()
    img.draw_string(240, 10, f"FPS{fps:.1f}", image.Color.from_rgb(255, 255, 0), scale=1)
    disp.show(img)

# 资源释放
cam.close()
disp.close()
serial.close()
print("程序结束，资源已释放")