from maix import camera, display, image, nn, app, time, uart, gpio, pinmap, touchscreen
import struct
import sys
sys.path.append('/root/exam')
import serial_protocol
import math

def is_in_button(x, y, btn_pos):
    return (btn_pos[0] <= x <= btn_pos[0] + btn_pos[2] and 
            btn_pos[1] <= y <= btn_pos[1] + btn_pos[3])

# === 卡尔曼滤波类 ===
class KalmanFilter:
    def __init__(self, process_noise=0.1, measurement_noise=0.1):
        self.state = None
        self.covariance = None
        self.transition_matrix = [[1, 0, 1, 0],
                                 [0, 1, 0, 1],
                                 [0, 0, 1, 0],
                                 [0, 0, 0, 1]]
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.measurement_matrix = [[1, 0, 0, 0],
                                  [0, 1, 0, 0]]
        self.initialized = False
    
    def init(self, x, y):
        self.state = [x, y, 0, 0]
        self.covariance = [[1, 0, 0, 0],
                          [0, 1, 0, 0],
                          [0, 0, 1, 0],
                          [0, 0, 0, 1]]
        self.initialized = True
    
    def predict(self):
        if not self.initialized:
            return None
        
        new_state = [0]*4
        for i in range(4):
            new_state[i] = sum(self.transition_matrix[i][j] * self.state[j] for j in range(4))
        
        new_cov = [[0]*4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                new_cov[i][j] = sum(self.transition_matrix[i][k] * self.covariance[k][l] * self.transition_matrix[j][l] 
                                   for k in range(4) for l in range(4))
                if i == j:
                    new_cov[i][j] += self.process_noise
        
        self.state = new_state
        self.covariance = new_cov
        return (self.state[0], self.state[1])
    
    def update(self, x, y):
        if not self.initialized:
            self.init(x, y)
            return (x, y)
        
        S = [[0]*2 for _ in range(2)]
        for i in range(2):
            for j in range(2):
                S[i][j] = sum(self.measurement_matrix[i][k] * self.covariance[k][l] * self.measurement_matrix[j][l]
                             for k in range(4) for l in range(4))
                if i == j:
                    S[i][j] += self.measurement_noise
        
        K = [[0]*2 for _ in range(4)]
        for i in range(4):
            for j in range(2):
                K[i][j] = sum(self.covariance[i][k] * self.measurement_matrix[j][k] / S[j][j] for k in range(4))
        
        measurement = [x, y]
        innovation = [measurement[i] - sum(self.measurement_matrix[i][j] * self.state[j] for j in range(4)) for i in range(2)]
        for i in range(4):
            self.state[i] += sum(K[i][j] * innovation[j] for j in range(2))
        
        IKH = [[0]*4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                IKH[i][j] = (1 if i == j else 0) - sum(K[i][k] * self.measurement_matrix[k][j] for k in range(2))
        
        new_cov = [[0]*4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                new_cov[i][j] = sum(IKH[i][k] * self.covariance[k][j] for k in range(4))
        
        self.covariance = new_cov
        return (self.state[0], self.state[1])

# === 初始化配置 ===
detector = nn.YOLO11(model="/root/models/my_model1/yolo11n_int8.mud", dual_buff=True)
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

exit_label = "<Exit"
size = image.string_size(exit_label)
exit_btn_pos = [0, 0, _btn_width, _btn_height]

# === 变量初始化 ===
fps = 0
last_time = time.time()
frame_count = 0
red_center = None
green_center = None 
delta_x_red = 0   
delta_x_green = 0
light = 1
buzzle = 1
change_start = 1
fire_off = 0
fire_open = 0

kf_red = KalmanFilter()
kf_green = KalmanFilter()
kf_fire_off = KalmanFilter()
kf_fire_open = KalmanFilter()

track_history_red = []
track_history_green = []
max_history_length = 20

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
                    print(f'Received: qr_id={qr_id},cx={cx}, cy={cy}, to_stm32={to_stm32},color={color},light={light},buzzle={buzzle},change_start={change_start}')
                                 
                packet_len = comm_proto.length(data_buffer)
                if packet_len > 0:
                    data_buffer = data_buffer[packet_len:]
                else:
                    break
            else:
                break

    # === 图像处理 ===
    img = cam.read()
    objs = detector.detect(img, conf_th=0.5, iou_th=0.45)

    red_center = None
    green_center = None
    fire_off_center = None
    fire_open_center = None
    
    red_id = 1
    green_id = 2

    for obj in objs:
        label = detector.labels[obj.class_id].lower()
        cx = obj.x + obj.w // 2
        cy = obj.y + obj.h // 2

        if 'red' in label:
            if red_center is None:
                kf_red.init(cx, cy)
            else:
                cx, cy = kf_red.update(cx, cy)
            
            red_center = (int(cx), int(cy))
            delta_x_red = red_center[0]
            
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)
            img.draw_circle(red_center[0], red_center[1], 5, color=image.COLOR_RED)
            img.draw_string(red_center[0] - 10, red_center[1] - 15, f"RED ID:{red_id}", color=image.COLOR_RED)
            
            track_history_red.append(red_center)
            if len(track_history_red) > max_history_length:
                track_history_red.pop(0)
            
            for i in range(1, len(track_history_red)):
                img.draw_line(track_history_red[i-1][0], track_history_red[i-1][1],
                             track_history_red[i][0], track_history_red[i][1],
                             color=image.COLOR_RED, thickness=2)
        
        elif 'green' in label:
            if green_center is None:
                kf_green.init(cx, cy)
            else:
                cx, cy = kf_green.update(cx, cy)
            
            green_center = (int(cx), int(cy))
            delta_x_green = green_center[0]
            
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_GREEN)
            msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
            img.draw_string(obj.x, obj.y, msg, color=image.COLOR_GREEN)
            img.draw_circle(green_center[0], green_center[1], 5, color=image.COLOR_GREEN)
            img.draw_string(green_center[0] - 15, green_center[1] - 15, f"GREEN ID:{green_id}", color=image.COLOR_GREEN)
            
            track_history_green.append(green_center)
            if len(track_history_green) > max_history_length:
                track_history_green.pop(0)
            
            for i in range(1, len(track_history_green)):
                img.draw_line(track_history_green[i-1][0], track_history_green[i-1][1],
                             track_history_green[i][0], track_history_green[i][1],
                             color=image.COLOR_GREEN, thickness=2)
        
        elif 'fire_off' in label:
            if fire_off_center is None:
                kf_fire_off.init(cx, cy)
            else:
                cx, cy = kf_fire_off.update(cx, cy)
            
            fire_off_center = (int(cx), int(cy))
            fire_off = 1
            fire_open = 0
            
            coord_text = f"OFF:({int(cx)},{int(cy)})"
            img.draw_string(int(cx) - 30, int(cy) - 30, coord_text, color=image.COLOR_RED, scale=1.2)
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            img.draw_circle(int(cx), int(cy), 5, color=image.COLOR_RED)
        elif 'fire_open' in label:
            if fire_open_center is None:
                kf_fire_open.init(cx, cy)
            else:
                cx, cy = kf_fire_open.update(cx, cy)
            
            fire_open_center = (int(cx), int(cy))
            fire_open = 1
            fire_off = 0
            
            coord_text = f"ON:({int(cx)},{int(cy)})"
            img.draw_string(int(cx) - 30, int(cy) - 30, coord_text, color=image.COLOR_GREEN, scale=1.2)
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_GREEN)
            img.draw_circle(int(cx), int(cy), 5, color=image.COLOR_GREEN)

    # === 串口数据发送 ===
    if change_start:
        if red_center or green_center or fire_off_center or fire_open_center:
            if red_center:
                payload = struct.pack('<iii', red_id, delta_x_red, red_center[1])
            elif green_center:
                payload = struct.pack('<iii', green_id, delta_x_green, green_center[1])
            elif fire_off_center:
                payload = struct.pack('<iii', 3, fire_off_center[0], fire_off_center[1])
            else:
                payload = struct.pack('<iii', 4, fire_open_center[0], fire_open_center[1])
            encoded = comm_proto.encode(payload)
            serial.write(encoded)
        else:
            payload = struct.pack('<iii', 666, 666, 666)
            encoded = comm_proto.encode(payload)
            serial.write(encoded)

    # === GPIO控制 ===
    led.value(0)
    if fire_off:
        buzzles.value(0)
        led_red.value(0)
    elif fire_open:
        buzzles.value(1)
        led_red.value(1)

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

    # 退出按钮
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
        led_red.toggle()

    # === 显示信息 ===
    img.draw_string(240, 10, f"FPS{fps:.1f}", image.Color.from_rgb(255, 255, 0), scale=1)
    img.draw_string(240, 20, f"Red {delta_x_red:d}", image.Color.from_rgb(0, 255, 255), scale=1)
    img.draw_string(240, 30, f"Gre {delta_x_green:d}", image.Color.from_rgb(0, 255, 255), scale=1)
    img.draw_string(240, 40, f"OFF:{fire_off}", image.Color.from_rgb(255, 0, 0), scale=1)
    img.draw_string(240, 50, f"OPEN:{fire_open}", image.Color.from_rgb(0, 255, 0), scale=1)

    # === 显示图像 ===
    disp.show(img)

# 资源释放
cam.close()
disp.close()
print("程序结束，资源已释放")