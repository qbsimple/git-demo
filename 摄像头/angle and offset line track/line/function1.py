from maix import camera, image, time, app, uart
import math
import struct
import sys
sys.path.append('/root/exam')
from gui import GUI
import serial_protocol

# 屏幕宽度和高度
IMAGE_WIDTH = 320
IMAGE_HEIGHT = 240
BTN_WIDTH = IMAGE_WIDTH // 6
BTN_HEIGHT = IMAGE_HEIGHT // 6

# 按钮ID和状态
BTN_ID_PIXEL = -1
BTN_ID_BINARY = -1
TO_SHOW_BINARY = False
TO_GET_PIXEL = False

# 初始化串口通信协议
comm_proto = serial_protocol.SerialProtocol()
# 初始化串口
device = "/dev/ttyS0"
serial = uart.UART(device, 115200)

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
    threshold = [0, 30, -20, 20, -20, 20]  # 默认阈值

    keys = ['lmin', 'lmax', 'amin', 'amax', 'bmin', 'bmax']
    for i, key in enumerate(keys):
        value_str = app.get_app_config_kv('demo_find_line', key, '', False)
        if value_str:
            threshold[i] = int(value_str)
    
    return threshold

def btn_pressed(btn_id, state):
    '''
    界面上按键的状态改变回调函数
    '''
    global TO_SHOW_BINARY, TO_GET_PIXEL, BTN_ID_BINARY, BTN_ID_PIXEL
    if state == 0:  # 只响应触摸抬起的动作
        return 

    if btn_id == BTN_ID_BINARY:
        TO_SHOW_BINARY = not TO_SHOW_BINARY
        if TO_GET_PIXEL:
            TO_GET_PIXEL = False
    elif btn_id == BTN_ID_PIXEL:
        TO_GET_PIXEL = not TO_GET_PIXEL

def send_line_data(angle, offset):
    '''
    将线条的角度和偏移量打包并通过串口发送
    '''
    # 限制offset的范围，防止异常值
    offset = max(min(offset, 160), -160)  # 限制在±160范围内（图像宽度的一半）
    
    # 打包数据：角度（float）和偏移量（int）
    payload = struct.pack('<fi', angle, int(offset))  # 确保offset是整数
    encoded = comm_proto.encode(payload)
    serial.write(encoded)
    print(f"Sent data: angle={angle:.2f}, offset={offset}")

def main():
    global TO_SHOW_BINARY, TO_GET_PIXEL, BTN_ID_BINARY, BTN_ID_PIXEL

    print(app.get_app_config_path())
    cam = camera.Camera(IMAGE_WIDTH, IMAGE_HEIGHT) 
    gui = GUI()

    BTN_ID_PIXEL = gui.createButton(0, IMAGE_HEIGHT - BTN_HEIGHT, BTN_WIDTH, BTN_HEIGHT)
    gui.setItemLabel(BTN_ID_PIXEL, '取阈值')
    gui.setItemCallback(BTN_ID_PIXEL, btn_pressed)

    BTN_ID_BINARY = gui.createButton(IMAGE_WIDTH - BTN_WIDTH, IMAGE_HEIGHT - BTN_HEIGHT, BTN_WIDTH, BTN_HEIGHT)
    gui.setItemLabel(BTN_ID_BINARY, '二值化')
    gui.setItemCallback(BTN_ID_BINARY, btn_pressed)

    last_x, last_y = -1, -1
    threshold = get_configured_threshold()
    print(threshold)

    while not app.need_exit():
        # 1. 读取图像
        img = cam.read()
        if TO_SHOW_BINARY:
            img = img.binary([threshold], False)
        
        # 2. 图像取阈值
        if TO_GET_PIXEL:
            x, y = gui.get_touch()
            if last_x != x or last_y != y:
                last_x, last_y = x, y

                rgb = img.get_pixel(x, y, True)
                lab = rgb_to_lab(rgb)
                if len(lab) >= 3:
                    threshold[0] = max(math.floor(lab[0]) - 30, 0)
                    threshold[1] = min(math.ceil(lab[0]) + 30, 100)
                    threshold[2] = max(math.floor(lab[1]) - 10, -128)
                    threshold[3] = min(math.ceil(lab[1]) + 10, 127)
                    threshold[4] = max(math.floor(lab[2]) - 10, -128)
                    threshold[5] = min(math.ceil(lab[2]) + 10, 127)
                    print(threshold)
                    set_configured_threshold(threshold)
            img.draw_cross(x, y, image.COLOR_YELLOW, 8, 2)
        
        # 3. 线性回归寻迹画线
        area_threshold = 100
        lines = img.get_regression([threshold], area_threshold=area_threshold, pixels_threshold=area_threshold)
        for line in lines:
            img.draw_line(line.x1(), line.y1(), line.x2(), line.y2(), image.COLOR_GREEN, 2)
            img.draw_string(0, 0, f'mag:{line.magnitude()}  theta:{line.theta()}  rho:{line.rho()}')

            # 计算线条的角度和偏移量
            angle = line.theta()  # 线条角度
            offset = line.x1() - IMAGE_WIDTH // 2  # 线条中心相对于图像中心的偏移量

            # 发送数据给单片机
            send_line_data(angle, offset)

        # 4. 更新显示    
        gui.run(img)

if __name__ == '__main__':
    main()





