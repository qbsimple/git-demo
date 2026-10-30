from maix import camera, display, image, nn, app, time, uart, gpio, pinmap, touchscreen
import struct
import sys
sys.path.append('/root/exam')
import serial_protocol

def is_in_button(x, y, btn_pos):
    """优化后的按钮区域检测（使用边界预计算）"""
    x1, y1, w, h = btn_pos
    x2, y2 = x1 + w, y1 + h
    return x1 <= x <= x2 and y1 <= y <= y2

# === 初始化配置 === 
detector = nn.YOLO11(model="/root/models/my_model1_2022/yolo11n_int8.mud", dual_buff=True)
disp = display.Display()
cam = camera.Camera(320, 240, fps=60)

# === 串口通信配置 ===
comm_proto = serial_protocol.SerialProtocol()
device = "/dev/ttyS0"
serial = uart.UART(device, 500000)
data_buffer = bytes()

# === GPIO配置 ===
pinmap.set_pin_function("B3", "GPIOB3")
led = gpio.GPIO("GPIOB3", gpio.Mode.OUT)
led.value(0)

pinmap.set_pin_function("A15", "GPIOA15")
buzzles = gpio.GPIO("GPIOA15", gpio.Mode.OUT)
buzzles.value(1)

pinmap.set_pin_function("A18", "GPIOA18")
led_red = gpio.GPIO("GPIOA18", gpio.Mode.OUT)
led_red.value(1)

# === 触摸屏优化 ===
class TouchController:
    def __init__(self):
        self.ts = touchscreen.TouchScreen()
        self.last_state = (0, 0, False)
        self.debounce_ms = 30  # 防抖时间30ms
        self.last_touch_time = 0
        
    def read(self):
        """带防抖的触摸读取"""
        x, y, pressed = self.ts.read()
        curr_time = time.ticks_ms()
        
        # 防抖处理
        if pressed and (curr_time - self.last_touch_time) < self.debounce_ms:
            return self.last_state
            
        self.last_state = (x, y, pressed)
        self.last_touch_time = curr_time
        return x, y, pressed

touch = TouchController()

# === 按钮配置 ===
_image_width = 320
_image_height = 240
_btn_width = _image_width // 6
_btn_height = _image_height // 7

id_btns = [
    {"id": 1, "label": "RedC", "pos": [0, 0, _btn_width, _btn_height]},
    {"id": 2, "label": "RedT", "pos": [_btn_width, 0, _btn_width, _btn_height]},
    {"id": 3, "label": "RedS", "pos": [2*_btn_width, 0, _btn_width, _btn_height]},
    {"id": 4, "label": "BlueC", "pos": [3*_btn_width, 0, _btn_width, _btn_height]},
    {"id": 5, "label": "BlueT", "pos": [4*_btn_width, 0, _btn_width, _btn_height]},
    {"id": 6, "label": "BlueS", "pos": [5*_btn_width, 0, _btn_width, _btn_height]}
]
selected_id = 0  # 0表示显示全部

# === 变量初始化 ===
fps = 0
last_time = time.time()
frame_count = 0
light = 1
buzzle = 1
change_start = 1

while not app.need_exit():
    # === 串口处理（保持原样）===
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
                    qr_id, cx, cy, to_stm32, color, light, buzzle, change_start = struct.unpack('<iiiiiiii', result)
                packet_len = comm_proto.length(data_buffer)
                if packet_len > 0:
                    data_buffer = data_buffer[packet_len:]
                else:
                    break
            else:
                break

    # === 图像采集 ===
    img = cam.read()

    # === 优化触摸处理 ===
    x, y, pressed = touch.read()
    if pressed:
        # 坐标转换到图像空间
        x, y = image.resize_map_pos_reverse(img.width(), img.height(), 
                                          disp.width(), disp.height(),
                                          image.Fit.FIT_CONTAIN, x, y)
        
        # 按钮检测
        for btn in id_btns:
            if is_in_button(x, y, btn["pos"]):
                selected_id = btn["id"] if selected_id != btn["id"] else 0
                break

    # === 图形检测 ===
    objs = detector.detect(img, conf_th=0.6, iou_th=0.45)
    
    # 初始化中心点
    red_yuan_center = red_sanjiao_center = red_zhengfang_center = None
    blue_yuan_center = blue_sanjiao_center = blue_zhengfang_center = None

    for obj in objs:
        label = detector.labels[obj.class_id].lower()
        cx = obj.x + obj.w // 2
        cy = obj.y + obj.h // 2

        # 根据selected_id过滤
        if selected_id != 0:
            if (selected_id == 1 and 'red_yuan' not in label) or \
               (selected_id == 2 and 'red_sanjiao' not in label) or \
               (selected_id == 3 and 'red_zhengfang' not in label) or \
               (selected_id == 4 and 'blue_yuan' not in label) or \
               (selected_id == 5 and 'blue_sanjiao' not in label) or \
               (selected_id == 6 and 'blue_zhengfang' not in label):
                continue

        # 红色圆形 (ID 1)
        if 'red_yuan' in label:
            red_yuan_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_yuan_center[0], red_yuan_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_yuan_center[0]-10, red_yuan_center[1]-15, f"ID:1", color=image.COLOR_RED)
        
        # 其他图形检测（保持原有完整逻辑）
        # [红色三角形、红色正方形、蓝色圆形、蓝色三角形、蓝色正方形...]
        elif 'red_sanjiao' in label:
            red_sanjiao_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_sanjiao_center[0], red_sanjiao_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_sanjiao_center[0]-15, red_sanjiao_center[1]-15, f"ID:2", color=image.COLOR_RED)

        elif 'red_zhengfang' in label:
            red_zhengfang_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_zhengfang_center[0], red_zhengfang_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_zhengfang_center[0]-15, red_zhengfang_center[1]-15, f"ID:3", color=image.COLOR_RED)

        elif 'blue_yuan' in label:
            blue_yuan_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_yuan_center[0], blue_yuan_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_yuan_center[0]-10, blue_yuan_center[1]-15, f"ID:4", color=image.COLOR_BLUE)

        elif 'blue_sanjiao' in label:
            blue_sanjiao_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_sanjiao_center[0], blue_sanjiao_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_sanjiao_center[0]-15, blue_sanjiao_center[1]-15, f"ID:5", color=image.COLOR_BLUE)

        elif 'blue_zhengfang' in label:
            blue_zhengfang_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_zhengfang_center[0], blue_zhengfang_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_zhengfang_center[0]-15, blue_zhengfang_center[1]-15, f"ID:6", color=image.COLOR_BLUE)

    # === 串口发送（保持原样）===
    if change_start:
        if selected_id == 0 or \
           (selected_id == 1 and red_yuan_center) or \
           (selected_id == 2 and red_sanjiao_center) or \
           (selected_id == 3 and red_zhengfang_center) or \
           (selected_id == 4 and blue_yuan_center) or \
           (selected_id == 5 and blue_sanjiao_center) or \
           (selected_id == 6 and blue_zhengfang_center):
            
            if selected_id == 1 and red_yuan_center:
                payload = struct.pack('<iii', 1, red_yuan_center[0], red_yuan_center[1])
            elif selected_id == 2 and red_sanjiao_center:
                payload = struct.pack('<iii', 2, red_sanjiao_center[0], red_sanjiao_center[1])
            elif selected_id == 3 and red_zhengfang_center:
                payload = struct.pack('<iii', 3, red_zhengfang_center[0], red_zhengfang_center[1])
            elif selected_id == 4 and blue_yuan_center:
                payload = struct.pack('<iii', 4, blue_yuan_center[0], blue_yuan_center[1])
            elif selected_id == 5 and blue_sanjiao_center:
                payload = struct.pack('<iii', 5, blue_sanjiao_center[0], blue_sanjiao_center[1])
            elif selected_id == 6 and blue_zhengfang_center:
                payload = struct.pack('<iii', 6, blue_zhengfang_center[0], blue_zhengfang_center[1])
            else:
                if red_yuan_center:
                    payload = struct.pack('<iii', 1, red_yuan_center[0], red_yuan_center[1])
                elif red_sanjiao_center:
                    payload = struct.pack('<iii', 2, red_sanjiao_center[0], red_sanjiao_center[1])
                elif red_zhengfang_center:
                    payload = struct.pack('<iii', 3, red_zhengfang_center[0], red_zhengfang_center[1])
                elif blue_yuan_center:
                    payload = struct.pack('<iii', 4, blue_yuan_center[0], blue_yuan_center[1])
                elif blue_sanjiao_center:
                    payload = struct.pack('<iii', 5, blue_sanjiao_center[0], blue_sanjiao_center[1])
                elif blue_zhengfang_center:
                    payload = struct.pack('<iii', 6, blue_zhengfang_center[0], blue_zhengfang_center[1])
                else:
                    payload = struct.pack('<iii', 666, 666, 666)
                
            serial.write(comm_proto.encode(payload))
        else:
            serial.write(comm_proto.encode(struct.pack('<iii', 666, 666, 666)))

    # === 按钮绘制 ===
    for btn in id_btns:
        color = image.COLOR_GREEN if selected_id == btn["id"] else image.COLOR_WHITE
        img.draw_rect(btn["pos"][0], btn["pos"][1], btn["pos"][2], btn["pos"][3], color, 2)
        img.draw_string(btn["pos"][0]+5, btn["pos"][1]+12, btn["label"], color)

    # === 帧率计算 ===
    frame_count += 1
    current_time = time.time()
    if current_time - last_time >= 1.0:
        fps = frame_count / (current_time - last_time)
        frame_count = 0
        last_time = current_time
        led_red.toggle()

    # 显示信息
    img.draw_string(220, 260, f"FPS:{fps:.1f}", image.COLOR_YELLOW)
    img.draw_string(220, 270, f"SelID:{selected_id}", image.COLOR_WHITE)

    # === 显示 ===
    disp.show(img)

# 资源释放
cam.close()
disp.close()
print("程序退出")