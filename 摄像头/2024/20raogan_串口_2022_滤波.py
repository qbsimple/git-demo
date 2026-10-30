from maix import camera, display, image, nn, app, time, uart, gpio, pinmap, touchscreen
import struct
import sys
from collections import deque  # 用于移动平均滤波

sys.path.append('/root/exam')
import serial_protocol

def is_in_button(x, y, btn_pos):
    """检查触摸点�?否在按钮区域�?"""
    return (btn_pos[0] <= x <= btn_pos[0] + btn_pos[2] and 
            btn_pos[1] <= y <= btn_pos[1] + btn_pos[3])

# === 移动平均滤波�? ===
class MovingAverageFilter:
    def __init__(self, window_size=10):
        self.window_size = window_size
        self.x_history = deque(maxlen=window_size)
        self.y_history = deque(maxlen=window_size)
    
    def update(self, x, y):
        """更新并返回滤波后的坐�?"""
        self.x_history.append(x)
        self.y_history.append(y)
        
        if len(self.x_history) == self.window_size:
            return sum(self.x_history)/self.window_size, sum(self.y_history)/self.window_size
        return x, y  # 窗口�?满时返回原�?��?

# === 初�?�化配置 ===
detector = nn.YOLO11(model="/root/models/my_model1_2022/yolo11n_int8.mud", dual_buff=True)
disp = display.Display()
cam = camera.Camera(320, 240, fps=60)

# === 初�?�化滤波�? ===
filters = {
    'red_yuan': MovingAverageFilter(),
    'red_sanjiao': MovingAverageFilter(),
    'red_zhengfang': MovingAverageFilter(),
    'blue_yuan': MovingAverageFilter(),
    'blue_sanjiao': MovingAverageFilter(),
    'blue_zhengfang': MovingAverageFilter()
}

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
buzzles.value(0)

pinmap.set_pin_function("A28", "GPIOA22")
buzzles_big = gpio.GPIO("GPIOA22", gpio.Mode.OUT)
buzzles_big .value(0)


pinmap.set_pin_function("A18", "GPIOA18")
led_red = gpio.GPIO("GPIOA18", gpio.Mode.OUT)
led_red.value(1)






# === 触摸屏配�? ===
ts = touchscreen.TouchScreen() 
torch_flag = False
torch_success = False
_image_width = 320
_image_height = 240
_btn_width = _image_width // 6
_btn_height = _image_height // 7
CROSS_COLOR = image.COLOR_YELLOW    # 十字标�?��?�色
CROSS_SIZE = 12                     # 十字线长�?
exit_label = "<exit"
exit_btn_pos = [0, 0, _btn_width, _btn_height]

# === 变量初�?�化 ===
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

    # 初�?�化各�?�形状的�?心点
    red_yuan_center = None
    red_sanjiao_center = None
    red_zhengfang_center = None
    blue_yuan_center = None
    blue_sanjiao_center = None
    blue_zhengfang_center = None
    
    # 为每种形状分配ID
    red_yuan_id = 1
    red_sanjiao_id = 2
    red_zhengfang_id = 3
    blue_yuan_id = 4
    blue_sanjiao_id = 5
    blue_zhengfang_id = 6

    for obj in objs:
        label = detector.labels[obj.class_id].lower()

        cx = obj.x + obj.w // 2
        cy = obj.y + obj.h // 2
        if 140<cx<180 and 92<cy<132:
            buzzles_big .value(1)
        else:
            buzzles_big .value(0)
        img.draw_line(cx-CROSS_SIZE, cy, cx+CROSS_SIZE, cy, CROSS_COLOR, 2)
        img.draw_line(cx, cy-CROSS_SIZE, cx, cy+CROSS_SIZE, CROSS_COLOR, 2)        


        # 应用移动平均滤波
        if 'red_yuan' in label:
            filtered_x, filtered_y = filters['red_yuan'].update(cx, cy)
            red_yuan_center = (int(filtered_x), int(filtered_y))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_yuan_center[0], red_yuan_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_yuan_center[0] - 10, red_yuan_center[1] - 15, f" ID:{red_yuan_id}", color=image.COLOR_RED)
        
        elif 'red_sanjiao' in label:
            filtered_x, filtered_y = filters['red_sanjiao'].update(cx, cy)
            red_sanjiao_center = (int(filtered_x), int(filtered_y))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_sanjiao_center[0], red_sanjiao_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_sanjiao_center[0] - 15, red_sanjiao_center[1] - 15, f" ID:{red_sanjiao_id}", color=image.COLOR_RED)
        
        elif 'red_zhengfang' in label:
            filtered_x, filtered_y = filters['red_zhengfang'].update(cx, cy)
            red_zhengfang_center = (int(filtered_x), int(filtered_y))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_zhengfang_center[0], red_zhengfang_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_zhengfang_center[0] - 15, red_zhengfang_center[1] - 15, f" ID:{red_zhengfang_id}", color=image.COLOR_RED)
        
        elif 'blue_yuan' in label:
            filtered_x, filtered_y = filters['blue_yuan'].update(cx, cy)
            blue_yuan_center = (int(filtered_x), int(filtered_y))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_yuan_center[0], blue_yuan_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_yuan_center[0] - 10, blue_yuan_center[1] - 15, f" ID:{blue_yuan_id}", color=image.COLOR_BLUE)
        
        elif 'blue_sanjiao' in label:
            filtered_x, filtered_y = filters['blue_sanjiao'].update(cx, cy)
            blue_sanjiao_center = (int(filtered_x), int(filtered_y))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_sanjiao_center[0], blue_sanjiao_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_sanjiao_center[0] - 15, blue_sanjiao_center[1] - 15, f" ID:{blue_sanjiao_id}", color=image.COLOR_BLUE)
        
        elif 'blue_zhengfang' in label:
            filtered_x, filtered_y = filters['blue_zhengfang'].update(cx, cy)
            blue_zhengfang_center = (int(filtered_x), int(filtered_y))
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_BLUE)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_BLUE)
            img.draw_circle(blue_zhengfang_center[0], blue_zhengfang_center[1], 5, color=image.COLOR_BLUE)
            img.draw_string(blue_zhengfang_center[0] - 15, blue_zhengfang_center[1] - 15, f" ID:{blue_zhengfang_id}", color=image.COLOR_BLUE)

    # === 串口数据发�? ===
    if change_start:
        if (red_yuan_center or red_sanjiao_center or red_zhengfang_center or 
            blue_yuan_center or blue_sanjiao_center or blue_zhengfang_center):
            
            if red_yuan_center:
                payload = struct.pack('<iii', red_yuan_id, red_yuan_center[0], red_yuan_center[1])
            elif red_sanjiao_center:
                payload = struct.pack('<iii', red_sanjiao_id, red_sanjiao_center[0], red_sanjiao_center[1])
            elif red_zhengfang_center:
                payload = struct.pack('<iii', red_zhengfang_id, red_zhengfang_center[0], red_zhengfang_center[1])
            elif blue_yuan_center:
                payload = struct.pack('<iii', blue_yuan_id, blue_yuan_center[0], blue_yuan_center[1])
            elif blue_sanjiao_center:
                payload = struct.pack('<iii', blue_sanjiao_id, blue_sanjiao_center[0], blue_sanjiao_center[1])
            elif blue_zhengfang_center:
                payload = struct.pack('<iii', blue_zhengfang_id, blue_zhengfang_center[0], blue_zhengfang_center[1])
                
            encoded = comm_proto.encode(payload)
            serial.write(encoded)
        else:
            payload = struct.pack('<iii', 666, 666, 666)
            encoded = comm_proto.encode(payload)
            serial.write(encoded)

    # === 触摸屏�?�理 ===
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

    # 退出按�?
    img.draw_string(8, 12, exit_label, image.Color.from_rgb(255, 0, 255))
    img.draw_rect(exit_btn_pos[0], exit_btn_pos[1], exit_btn_pos[2], exit_btn_pos[3], image.Color.from_rgb(255, 0, 255), 2)
    if torch_success == True and is_in_button(x, y, exit_btn_pos):
        torch_success = False
        app.set_exit_flag(True)

    # === 帧率计算 ===
    frame_count += 1
    current_time = time.time()
    elapsed_time = current_time - last_time
    if elapsed_time >= 1.0:
        fps = frame_count / elapsed_time
        frame_count = 0
        last_time = current_time
   

    # === 显示信息 ===
    img.draw_string(220, 10, f"FPS:{fps:.1f}", image.Color.from_rgb(255, 255, 0), scale=1)
    img.draw_string(220, 20, f"RedC:{red_yuan_center}" if red_yuan_center else "0", image.Color.from_rgb(255, 0, 0), scale=0.5)
    img.draw_string(220, 30, f"RedT:{red_sanjiao_center}" if red_sanjiao_center else "0", image.Color.from_rgb(255, 0, 0), scale=0.5)
    img.draw_string(220, 40, f"RedS:{red_zhengfang_center}" if red_zhengfang_center else "0", image.Color.from_rgb(255, 0, 0), scale=0.5)
    img.draw_string(220, 50, f"BlueC:{blue_yuan_center}" if blue_yuan_center else "0", image.Color.from_rgb(0, 0, 255), scale=0.5)
    img.draw_string(220, 60, f"BlueT:{blue_sanjiao_center}" if blue_sanjiao_center else "0", image.Color.from_rgb(0, 0, 255), scale=0.5)
    img.draw_string(220, 70, f"BlueS:{blue_zhengfang_center}" if blue_zhengfang_center else "0", image.Color.from_rgb(0, 0, 255), scale=0.5)

    # === 显示图像 ===
    disp.show(img)

# 资源释放
cam.close()
disp.close()
print("程序结束，资源已释放")