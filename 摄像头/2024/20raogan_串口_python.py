from maix import camera, display, image, nn, app, time, uart, gpio, pinmap, touchscreen
import struct
import sys
sys.path.append('/root/exam')
import serial_protocol

# ===== 常量定义 =====
# 模型路径
MODEL_PATH = "/root/models/my_model1/yolo11n_int8.mud"

# 串口配置
UART_DEVICE = "/dev/ttyS0"
UART_BAUDRATE = 500000

# 图像尺寸
IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240

# 按钮尺寸
BTN_WIDTH = IMAGE_WIDTH // 6
BTN_HEIGHT = IMAGE_HEIGHT // 7

# 颜色定义
COLOR_RED = image.COLOR_RED
COLOR_GREEN = image.COLOR_GREEN
COLOR_CYAN = image.Color.from_rgb(0, 255, 255)
COLOR_YELLOW = image.Color.from_rgb(255, 255, 0)
COLOR_MAGENTA = image.Color.from_rgb(255, 0, 255)

# ===== 初始化函数 =====
def init_hardware():
    """初始化所有硬件设备"""
    # 摄像头和显示
    cam = camera.Camera(IMAGE_WIDTH, IMAGE_HEIGHT, fps=60)
    disp = display.Display()
    
    # 神经网络模型
    detector = nn.YOLO11(model=MODEL_PATH, dual_buff=True)
    
    # 串口通信
    serial = uart.UART(UART_DEVICE, UART_BAUDRATE)
    comm_proto = serial_protocol.SerialProtocol()
    
    # GPIO初始化
    pinmap.set_pin_function("B3", "GPIOB3")
    led = gpio.GPIO("GPIOB3", gpio.Mode.OUT)
    led.value(0)
    
    pinmap.set_pin_function("A15", "GPIOA15")
    buzzers = gpio.GPIO("GPIOA15", gpio.Mode.OUT)
    buzzers.value(1)
    
    pinmap.set_pin_function("A18", "GPIOA18")
    led_red = gpio.GPIO("GPIOA18", gpio.Mode.OUT)
    led_red.value(1)
    
    # 触摸屏
    ts = touchscreen.TouchScreen()
    
    return cam, disp, detector, serial, comm_proto, led, buzzers, led_red, ts

# ===== 对象检测和绘制函数 =====
def detect_and_draw_objects(img, detector):
    """检测对象并在图像上绘制结果"""
    objs = detector.detect(img, conf_th=0.5, iou_th=0.45)
    
    detected_objects = {
        'red': None,
        'green': None,
        'fire_off': None,
        'fire_open': None
    }
    
    for obj in objs:
        label = detector.labels[obj.class_id].lower()
        cx = obj.x + obj.w // 2
        cy = obj.y + obj.h // 2
        
        if 'red' in label:
            detected_objects['red'] = (cx, cy)
            draw_object(img, obj, cx, cy, COLOR_RED, f"RED ID:1")
        elif 'green' in label:
            detected_objects['green'] = (cx, cy)
            draw_object(img, obj, cx, cy, COLOR_GREEN, f"GREEN ID:2")
        elif 'fire_off' in label:
            detected_objects['fire_off'] = (cx, cy)
            draw_status(img, cx, cy, f"OFF:({cx},{cy})", COLOR_RED)
        elif 'fire_open' in label:
            detected_objects['fire_open'] = (cx, cy)
            draw_status(img, cx, cy, f"ON:({cx},{cy})", COLOR_GREEN)
    
    return detected_objects

def draw_object(img, obj, cx, cy, color, label_text):
    """绘制检测到的对象"""
    img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=color)
    msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
    img.draw_string(obj.x, obj.y, msg, color=color)
    img.draw_circle(cx, cy, 5, color=color)
    img.draw_string(cx - 10, cy - 15, label_text, color=color)

def draw_status(img, cx, cy, text, color):
    """绘制状态信息"""
    img.draw_string(cx - 30, cy - 30, text, color=color, scale=1.2)
    img.draw_circle(cx, cy, 5, color=color)

# ===== 串口处理函数 =====
def process_serial_data(serial, comm_proto, data_buffer):
    """处理串口接收到的数据"""
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
                    print(f'Received: qr_id={qr_id},cx={cx}, cy={cy}, to_stm32={to_stm32},color={color},light={light},buzzle={buzzle},change_start={change_start}')
                                 
                packet_len = comm_proto.length(data_buffer)
                if packet_len > 0:
                    data_buffer = data_buffer[packet_len:]
                else:
                    break
            else:
                break
    
    return data_buffer

def send_detection_data(serial, comm_proto, detected_objects, change_start):
    """发送检测到的对象数据"""
    if not change_start:
        return
    
    if detected_objects['red']:
        payload = struct.pack('<iii', 1, *detected_objects['red'])
    elif detected_objects['green']:
        payload = struct.pack('<iii', 2, *detected_objects['green'])
    elif detected_objects['fire_off']:
        payload = struct.pack('<iii', 3, *detected_objects['fire_off'])
    elif detected_objects['fire_open']:
        payload = struct.pack('<iii', 4, *detected_objects['fire_open'])
    else:
        payload = struct.pack('<iii', 666, 666, 666)
    
    encoded = comm_proto.encode(payload)
    serial.write(encoded)

# ===== 触摸屏处理函数 =====
def is_in_button(x, y, btn_pos):
    """检查触摸点是否在按钮区域内"""
    return (btn_pos[0] <= x <= btn_pos[0] + btn_pos[2] and 
            btn_pos[1] <= y <= btn_pos[1] + btn_pos[3])

def handle_touchscreen(ts, img, exit_btn_pos):
    """处理触摸屏输入"""
    x, y, pressed = ts.read()
    x, y = image.resize_map_pos_reverse(
        img.width(), img.height(), 
        disp.width(), disp.height(), 
        image.Fit.FIT_CONTAIN, x, y
    )
    
    # 绘制触摸点
    img.draw_circle(x, y, 1, image.Color.from_rgb(255, 255, 255), 2)
    
    # 绘制退出按钮
    img.draw_string(8, 12, "<Exit", COLOR_MAGENTA)
    img.draw_rect(*exit_btn_pos, COLOR_MAGENTA, 2)
    
    # 检查是否点击了退出按钮
    if pressed and is_in_button(x, y, exit_btn_pos):
        app.set_exit_flag(True)
    
    return x, y, pressed

# ===== 主程序 =====
if __name__ == "__main__":
    # 初始化硬件
    cam, disp, detector, serial, comm_proto, led, buzzers, led_red, ts = init_hardware()
    
    # 变量初始化
    data_buffer = bytes()
    exit_btn_pos = [0, 0, BTN_WIDTH, BTN_HEIGHT]
    fps = 0
    last_time = time.time()
    frame_count = 0
    
    try:
        while not app.need_exit():
            # 帧率计算
            frame_count += 1
            current_time = time.time()
            elapsed_time = current_time - last_time
            if elapsed_time >= 1.0:
                fps = frame_count / elapsed_time
                frame_count = 0
                last_time = current_time
                led_red.toggle()
            
            # 处理串口数据
            data_buffer = process_serial_data(serial, comm_proto, data_buffer)
            
            # 图像采集和处理
            img = cam.read()
            detected_objects = detect_and_draw_objects(img, detector)
            
            # 发送检测数据
            send_detection_data(serial, comm_proto, detected_objects, change_start=True)
            
            # 处理触摸屏输入
            handle_touchscreen(ts, img, exit_btn_pos)
            
            # 显示调试信息
            img.draw_string(220, 10, f"FPS{fps:.1f}", COLOR_YELLOW, scale=1)
            img.draw_string(220, 20, f"Red {detected_objects['red']}" if detected_objects['red'] else "Red None", COLOR_CYAN, scale=1)
            img.draw_string(220, 30, f"Gre {detected_objects['green']}" if detected_objects['green'] else "Gre None", COLOR_CYAN, scale=1)
            img.draw_string(220, 40, f"OFF:{detected_objects['fire_off']}" if detected_objects['fire_off'] else "OFF:None", COLOR_RED, scale=1)
            img.draw_string(220, 50, f"OPEN:{detected_objects['fire_open']}" if detected_objects['fire_open'] else "OPEN:None", COLOR_GREEN, scale=1)
            
            # 显示图像
            disp.show(img)
    
    finally:
        # 资源释放
        cam.close()
        disp.close()
        print("程序结束，资源已释放")