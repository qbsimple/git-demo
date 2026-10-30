from maix import camera, display, image, nn, app, time, uart, gpio, pinmap, touchscreen
import struct
import sys
sys.path.append('/root/exam')
import serial_protocol

def is_in_button(x, y, btn_pos):
    """检查触摸点是否在按钮区域内"""
    return (btn_pos[0] <= x <= btn_pos[0] + btn_pos[2] and 
            btn_pos[1] <= y <= btn_pos[1] + btn_pos[3])

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

# === 触摸屏配置 ===
ts = touchscreen.TouchScreen() 
torch_flag = False
torch_success = False
_image_width = 320
_image_height = 240
_btn_width = _image_width // 6
_btn_height = _image_height // 7

# === 按钮定义 ===
# 6个选择按钮
id_btns = [
    {"id": 1, "label": "RedC", "pos": [0, 0, _btn_width, _btn_height], "active": False},
    {"id": 2, "label": "RedT", "pos": [_btn_width, 0, _btn_width, _btn_height], "active": False},
    {"id": 3, "label": "RedS", "pos": [2*_btn_width, 0, _btn_width, _btn_height], "active": False},
    {"id": 4, "label": "BlueC", "pos": [3*_btn_width, 0, _btn_width, _btn_height], "active": False},
    {"id": 5, "label": "BlueT", "pos": [4*_btn_width, 0, _btn_width, _btn_height], "active": False},
    {"id": 6, "label": "BlueS", "pos": [5*_btn_width, 0, _btn_width, _btn_height], "active": False}
]

# 默认全部显示
selected_id = 0  # 0表示显示全部

# === 变量初始化 ===
fps = 0
last_time = time.time()
frame_count = 0

light = 1
buzzle = 1
change_start = 1

while not app.need_exit():
    # === 串口数据接收处理 ===
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
                    print(f'接收数据: qr_id={qr_id},cx={cx}, cy={cy}, to_stm32={to_stm32},color={color},light={light},buzzle={buzzle},change_start={change_start}')
                                 
                packet_len = comm_proto.length(data_buffer)
                if packet_len > 0:
                    data_buffer = data_buffer[packet_len:]
                else:
                    break
            else:
                break

    # === 图像处理 ===
    img = cam.read()
    objs = detector.detect(img, conf_th=0.6, iou_th=0.45)

    # 初始化各种形状的中心点
    red_yuan_center = None      # 红色圆形 (ID 1)
    red_sanjiao_center = None   # 红色三角形 (ID 2)
    red_zhengfang_center = None # 红色正方形 (ID 3)
    blue_yuan_center = None     # 蓝色圆形 (ID 4)
    blue_sanjiao_center = None  # 蓝色三角形 (ID 5)
    blue_zhengfang_center = None # 蓝色正方形 (ID 6)
    
    for obj in objs:
        label = detector.labels[obj.class_id].lower()
        cx = obj.x + obj.w // 2
        cy = obj.y + obj.h // 2

        # 根据selected_id决定是否处理当前对象
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
            img.draw_string(red_yuan_center[0] - 10, red_yuan_center[1] - 15, f" ID:1", color=image.COLOR_RED)
        
        # 红色三角形 (ID 2)
        elif 'red_sanjiao' in label:
            red_sanjiao_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_sanjiao_center[0], red_sanjiao_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_sanjiao_center[0] - 15, red_sanjiao_center[1] - 15, f" ID:2", color=image.COLOR_RED)
        
        # 红色正方形 (ID 3)
        elif 'red_zhengfang' in label:
            red_zhengfang_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_zhengfang_center[0], red_zhengfang_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_zhengfang_center[0] - 15, red_zhengfang_center[1] - 15, f" ID:3", color=image.COLOR_RED)
        
        # 蓝色圆形 (ID 4)
        elif 'blue_yuan' in label:
            blue_yuan_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_yuan_center[0], blue_yuan_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_yuan_center[0] - 10, blue_yuan_center[1] - 15, f" ID:4", color=image.COLOR_BLUE)
        
        # 蓝色三角形 (ID 5)
        elif 'blue_sanjiao' in label:
            blue_sanjiao_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_sanjiao_center[0], blue_sanjiao_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_sanjiao_center[0] - 15, blue_sanjiao_center[1] - 15, f" ID:5", color=image.COLOR_BLUE)
        
        # 蓝色正方形 (ID 6)
        elif 'blue_zhengfang' in label:
            blue_zhengfang_center = (int(cx), int(cy))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_zhengfang_center[0], blue_zhengfang_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_zhengfang_center[0] - 15, blue_zhengfang_center[1] - 15, f" ID:6", color=image.COLOR_BLUE)

    # === 串口数据发送 ===
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
                # 如果没有选择特定ID或选择显示全部，发送所有检测到的图形
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
                
            encoded = comm_proto.encode(payload)
            serial.write(encoded)
        else:
            payload = struct.pack('<iii', 666, 666, 666)
            encoded = comm_proto.encode(payload)
            serial.write(encoded)

    # === 触摸屏处理 ===
    x, y, pressed = ts.read()
    x, y = image.resize_map_pos_reverse(img.width(), img.height(), disp.width(), disp.height(), image.Fit.FIT_CONTAIN, x, y)
    img.draw_circle(x, y, 1, image.Color.from_rgb(255, 255, 255), 2)
    
    if torch_flag == False and pressed:
        torch_flag = True
        torch_success = False
        print(x, y, pressed)
    if pressed == False and torch_flag:
        torch_flag = False  
        torch_success = True

    # 绘制按钮
    for btn in id_btns:
        color = image.Color.from_rgb(0, 255, 0) if selected_id == btn["id"] else image.Color.from_rgb(255, 255, 255)
        img.draw_string(btn["pos"][0] + 5, btn["pos"][1] + 12, btn["label"], color)
        img.draw_rect(btn["pos"][0], btn["pos"][1], btn["pos"][2], btn["pos"][3], color, 2)

    # 处理按钮点击
    if torch_success:
        torch_success = False
        for btn in id_btns:
            if is_in_button(x, y, btn["pos"]):
                selected_id = btn["id"] if selected_id != btn["id"] else 0  # 点击已选中的按钮则取消选择
                break

    # === 帧率计算 ===
    frame_count += 1
    current_time = time.time()
    elapsed_time = current_time - last_time
    if elapsed_time >= 1.0:
        fps = frame_count / elapsed_time
        frame_count = 0
        last_time = current_time
        led_red.toggle()

    # === 显示信息 ===
    img.draw_string(220, 10, f"FPS:{fps:.1f}", image.Color.from_rgb(255, 255, 0), scale=1)
    img.draw_string(220, 20, f"SelID:{selected_id}", image.Color.from_rgb(255, 255, 255), scale=1)
    img.draw_string(220, 30, f"RedC:{red_yuan_center}" if red_yuan_center else "0", image.Color.from_rgb(255, 0, 0), scale=0.5)
    img.draw_string(220, 40, f"RedT:{red_sanjiao_center}" if red_sanjiao_center else "0", image.Color.from_rgb(255, 0, 0), scale=0.5)
    img.draw_string(220, 50, f"RedS:{red_zhengfang_center}" if red_zhengfang_center else "0", image.Color.from_rgb(255, 0, 0), scale=0.5)
    img.draw_string(220, 60, f"BlueC:{blue_yuan_center}" if blue_yuan_center else "0", image.Color.from_rgb(0, 0, 255), scale=0.5)
    img.draw_string(220, 70, f"BlueT:{blue_sanjiao_center}" if blue_sanjiao_center else "0", image.Color.from_rgb(0, 0, 255), scale=0.5)
    img.draw_string(220, 80, f"BlueS:{blue_zhengfang_center}" if blue_zhengfang_center else "0", image.Color.from_rgb(0, 0, 255), scale=0.5)

    # === 显示图像 ===
    disp.show(img)

# 资源释放
cam.close()
disp.close()
print("程序结束，资源已释放")