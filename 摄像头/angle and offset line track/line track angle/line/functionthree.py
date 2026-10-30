from maix import camera, image, time, app, uart
import math
import struct
import sys
sys.path.append('/root/exam')
from gui import GUI
import serial_protocol
# 屏幕宽度和高度
_image_width  = 320
_image_height = 240
_btn_width  = _image_width // 6
_btn_height = _image_height // 6

_btn_id_pixel   = -1
_btn_id_binary  = -1
_to_show_binary = False
_to_get_pixel   = False
# 初始化串口通信协议
comm_proto = serial_protocol.SerialProtocol()
# 初始化串口
device = "/dev/ttyS0"
serial = uart.UART(device, 115200)

# 区域定义（像素值）
NEAR_REGION = [0, int(_image_height*0.6), _image_width, int(_image_height*0.4)]  # [x, y, width, height]
MID_REGION = [0, int(_image_height*0.3), _image_width, int(_image_height*0.3)]
FAR_REGION = [0, 0, _image_width, int(_image_height*0.3)]

def rgb_to_lab(rgb):
    '''
    实现RGB值到LAB值的转换
    '''
    # RGB到XYZ的转换矩阵
    M = [
        [0.412453, 0.357580, 0.180423],
        [0.212671, 0.715160, 0.072169],
        [0.019334, 0.119193, 0.950227]
    ]
    
    # 归一化RGB值
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    
    # 线性化RGB值
    r = r / 12.92 if r <= 0.04045 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.04045 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.04045 else ((b + 0.055) / 1.055) ** 2.4
    
    # 计算XYZ值
    X = M[0][0] * r + M[0][1] * g + M[0][2] * b
    Y = M[1][0] * r + M[1][1] * g + M[1][2] * b
    Z = M[2][0] * r + M[2][1] * g + M[2][2] * b
    
    # XYZ到LAB的转换
    X /= 0.95047
    Y /= 1.0
    Z /= 1.08883
    
    def f(t):
        return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116
    
    L = 116 * f(Y) - 16
    a = 500 * (f(X) - f(Y))
    b = 200 * (f(Y) - f(Z))
    
    return [L, a, b]

def set_configured_threshold(threshold):
    '''
    阈值参数信息存入配置文件
    '''
    if len(threshold) < 6:
        return 

    app.set_app_config_kv('demo_find_line', 'lmin', str(threshold[0]), False)
    app.set_app_config_kv('demo_find_line', 'lmax', str(threshold[1]), False)
    app.set_app_config_kv('demo_find_line', 'amin', str(threshold[2]), False)
    app.set_app_config_kv('demo_find_line', 'amax', str(threshold[3]), False)
    app.set_app_config_kv('demo_find_line', 'bmin', str(threshold[4]), False)
    app.set_app_config_kv('demo_find_line', 'bmax', str(threshold[5]), True)

def get_configured_threshold():
    '''
    获取所存储配置文件中的阈值参数
    '''
    # 调整 LAB 值以适应红色
    threshold = [20, 80, 30, 100, -50, 50]  # 红色在LAB空间中的典型值范围

    value_str = app.get_app_config_kv('demo_find_line', 'lmin','', False)
    if len(value_str) > 0:
        threshold[0] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'lmax','', False)
    if len(value_str) > 0:
        threshold[1] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'amin','', False)
    if len(value_str) > 0:
        threshold[2] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'amax','', False)
    if len(value_str) > 0:
        threshold[3] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'bmin','', False)
    if len(value_str) > 0:
        threshold[4] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'bmax','', False)
    if len(value_str) > 0:
        threshold[5] = int(value_str)
    return threshold

def btn_pressed(btn_id, state):
    '''
    界面上按键的状态改变回调函数
    '''
    global _to_show_binary, _to_get_pixel, _btn_id_binary, _btn_id_pixel
    if state == 0: #只响应触摸抬起的动作
        return 

    if btn_id == _btn_id_binary:
        _to_show_binary = not _to_show_binary
        if _to_get_pixel:
            _to_get_pixel = False
    elif btn_id == _btn_id_pixel:
        _to_get_pixel = not _to_get_pixel

def send_line_data(angle, offset):
    '''
    将线条的角度和偏移量打包并通过串口发送
    '''

    # 打包数据：角度（float）和偏移量（int）
    payload = struct.pack('<fi', angle, offset)
    encoded = comm_proto.encode(payload)
    serial.write(encoded)
    print(f"Sent data: angle={angle}, offset={offset}")

def is_red_color(rgb):
    '''
    判断是否为红色
    '''
    lab = rgb_to_lab(rgb)
    # 红色在LAB空间中的特征：
    # L: 20-80 (亮度适中)
    # a: 30-100 (红色分量高)
    # b: -50-50 (蓝色分量适中)
    return (20 <= lab[0] <= 80 and 
            30 <= lab[1] <= 100 and 
            -50 <= lab[2] <= 50)

# 线条检测和处理
def process_line_by_regions(img, threshold, area_threshold=100):
    # 确保ROI值为整数
    near_roi = [int(val) if isinstance(val, float) else val for val in NEAR_REGION]
    mid_roi = [int(val) if isinstance(val, float) else val for val in MID_REGION] 
    far_roi = [int(val) if isinstance(val, float) else val for val in FAR_REGION]
    
    # 1. 检测近区线条
    near_lines = img.get_regression([threshold], roi=near_roi, area_threshold=area_threshold, pixels_threshold=area_threshold)
    if near_lines:
        # 优先处理近区线条
        line = select_best_line(near_lines)
        if line:
            return line
        
    # 2. 如果近区没有线条，检测中区
    mid_lines = img.get_regression([threshold], roi=mid_roi, area_threshold=area_threshold, pixels_threshold=area_threshold)
    if mid_lines:
        line = select_best_line(mid_lines)
        if line:
            return line
        
    # 3. 如果中区也没有线条，检测远区
    far_lines = img.get_regression([threshold], roi=far_roi, area_threshold=area_threshold, pixels_threshold=area_threshold)
    if far_lines:
        line = select_best_line(far_lines)
        if line:
            return line
        
    # 没有检测到任何合适的线条
    return None

# 添加辅助函数用于选择最佳线条
def select_best_line(lines):
    '''
    选择最佳线条，排除干扰线
    '''
    best_line = None
    max_score = -1
    
    for line in lines:
        # 计算线条的基本特征
        x1, y1 = int(line.x1()), int(line.y1())
        x2, y2 = int(line.x2()), int(line.y2())
        length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        
        # 计算线条的连续性得分
        continuity_score = 0
        for i in range(5):
            x = int(x1 + (x2 - x1) * i / 4)
            y = int(y1 + (y2 - y1) * i / 4)
            rgb = img.get_pixel(x, y, True)
            if is_red_color(rgb):
                continuity_score += 1
        
        # 计算综合得分
        score = 0
        
        # 1. 长度得分（排除太短的线）
        if length < 50:  # 最小长度阈值
            continue
        score += length * 0.3
        
        # 2. 连续性得分（排除断断续续的线）
        score += continuity_score * 20
        
        # 3. 角度得分（优先选择接近垂直的线）
        angle_diff = abs(abs(angle) - 90)  # 与90度的差值
        if angle_diff < 30:  # 允许30度的偏差
            score += (30 - angle_diff) * 2
        
        # 4. 位置得分（优先选择靠近图像中心的线）
        center_x = (x1 + x2) / 2
        center_offset = abs(center_x - _image_width / 2)
        if center_offset < _image_width / 4:  # 中心区域
            score += 50
        
        # 更新最佳线条
        if score > max_score:
            max_score = score
            best_line = line
    
    return best_line

def main():
    global _to_show_binary, _to_get_pixel, _btn_id_binary, _btn_id_pixel, img  # 添加img为全局变量

    print(app.get_app_config_path())
    cam = camera.Camera(_image_width, _image_height) 
    gui = GUI()

    _btn_id_pixel = gui.createButton(0, _image_height-_btn_height, _btn_width, _btn_height)
    gui.setItemLabel(_btn_id_pixel, '取阈值')
    gui.setItemCallback(_btn_id_pixel, btn_pressed)

    _btn_id_binary = gui.createButton(_image_width-_btn_width, _image_height-_btn_height, _btn_width, _btn_height)
    gui.setItemLabel(_btn_id_binary, '二值化')
    gui.setItemCallback(_btn_id_binary, btn_pressed)

    last_x = -1
    last_y = -1
    threshold = get_configured_threshold()
    print("红色检测阈值:", threshold)
    
    # 定义三个区域的边界
    near_mid_boundary = int(_image_height * 0.6)  # 近区和中区的边界
    mid_far_boundary = int(_image_height * 0.3)   # 中区和远区的边界
    area_threshold = 100  # 定义area_threshold

    while not app.need_exit():
        # 1. 读取图像
        img = cam.read()  # 更新全局img变量
        if _to_show_binary:
            img = img.binary([threshold], False)
        
        # 画出三条红线区分区域
        img.draw_line(0, near_mid_boundary, _image_width, near_mid_boundary, image.COLOR_RED, 2)  # 近区和中区边界
        img.draw_line(0, mid_far_boundary, _image_width, mid_far_boundary, image.COLOR_RED, 2)    # 中区和远区边界
        img.draw_string(5, near_mid_boundary + 5, "近区", image.COLOR_RED, scale=1)
        img.draw_string(5, mid_far_boundary + 5, "中区", image.COLOR_RED, scale=1)
        img.draw_string(5, 5, "远区", image.COLOR_RED, scale=1)
        
        # 2. 图像取阈值
        if _to_get_pixel:
            x,y = gui.get_touch()
            if last_x != x or last_y != y:
                last_x = x
                last_y = y

                rgb = img.get_pixel(x, y, True)
                lab = rgb_to_lab(rgb)
                print(f"触摸点LAB值: L={lab[0]:.1f}, a={lab[1]:.1f}, b={lab[2]:.1f}")
                if len(lab) >= 3:
                    # 调整阈值以适应红色
                    threshold[0] = math.floor(lab[0]) - 30
                    threshold[0] = threshold[0] if threshold[0] >= 0 else 0

                    threshold[1] = math.ceil(lab[0]) + 30
                    threshold[1] = threshold[1] if threshold[1] <= 100 else 100
                    
                    threshold[2] = math.floor(lab[1]) - 20
                    threshold[2] = threshold[2] if threshold[2] >= -128 else -128

                    threshold[3] = math.ceil(lab[1]) + 20
                    threshold[3] = threshold[3] if threshold[3] <= 127 else 127

                    threshold[4] = math.floor(lab[2]) - 20
                    threshold[4] = threshold[4] if threshold[4] >= -128 else -128

                    threshold[5] = math.ceil(lab[2]) + 20
                    threshold[5] = threshold[5] if threshold[5] <= 127 else 127
                    print("新的阈值:", threshold)
                    set_configured_threshold(threshold)
            img.draw_cross(x, y, image.COLOR_YELLOW, 8, 2)
        
        # 3. 线性回归寻迹画线
        line = process_line_by_regions(img, threshold, area_threshold)
        if line:
            img.draw_line(line.x1(), line.y1(), line.x2(), line.y2(), image.COLOR_RED, 2)
            img.draw_string(0,0, 'mag:{}  theta:{}  rho:{}'.format(line.magnitude(), line.theta(), line.rho()))

            # 计算线条的角度和偏移量
            angle = line.theta()  # 线条角度
            offset = line.x1() - _image_width // 2  # 线条中心相对于图像中心的偏移量

            # 发送数据给单片机
            send_line_data(angle, offset)

        # 4. 更新显示    
        gui.run(img)

if __name__ == '__main__':
    main()





