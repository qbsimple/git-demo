import sys  # 导入系统模块，用于操作Python运行时环境
sys.path.append('/root/exam')  # 将自定义模块路径添加到系统路径中，以便导入自定义模块
from gui import GUI  # 从自定义模块gui中导入GUI类
from maix import camera, image, time, app  # 导入maix库中的摄像头、图像处理、时间和应用模块
import math  # 导入数学库，用于数学计算

# 屏幕宽度和高度
_image_width = 320  # 定义图像宽度为320像素
_image_height = 240  # 定义图像高度为240像素
_btn_width = _image_width // 6  # 按钮宽度为屏幕宽度的1/6
_btn_height = _image_height // 6  # 按钮高度为屏幕高度的1/6

# 全局变量，用于存储按钮ID和状态
_btn_id_pixel = -1  # “取阈值”按钮的ID，初始值为-1
_btn_id_binary = -1  # “二值化”按钮的ID，初始值为-1
_to_show_binary = False  # 是否显示二值化图像，初始值为False
_to_get_pixel = False  # 是否处于取阈值模式，初始值为False

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
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0  # 将RGB值归一化到[0, 1]范围
    
    # 线性化RGB值
    r = r / 12.92 if r <= 0.04045 else ((r + 0.055) / 1.055) ** 2.4  # 对R通道进行线性化
    g = g / 12.92 if g <= 0.04045 else ((g + 0.055) / 1.055) ** 2.4  # 对G通道进行线性化
    b = b / 12.92 if b <= 0.04045 else ((b + 0.055) / 1.055) ** 2.4  # 对B通道进行线性化
    
    # 计算XYZ值
    X = M[0][0] * r + M[0][1] * g + M[0][2] * b  # 计算X值
    Y = M[1][0] * r + M[1][1] * g + M[1][2] * b  # 计算Y值
    Z = M[2][0] * r + M[2][1] * g + M[2][2] * b  # 计算Z值
    
    # XYZ到LAB的转换
    X /= 0.95047  # 归一化X值
    Y /= 1.0  # 归一化Y值
    Z /= 1.08883  # 归一化Z值
    
    def f(t):
        return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116  # 定义辅助函数f(t)
    
    L = 116 * f(Y) - 16  # 计算L值
    a = 500 * (f(X) - f(Y))  # 计算a值
    b = 200 * (f(Y) - f(Z))  # 计算b值
    
    return [L, a, b]  # 返回LAB值

def set_configured_threshold(threshold):
    '''
    将阈值参数存入配置文件
    '''
    if len(threshold) < 6:  # 如果阈值参数不足6个，直接返回
        return 

    # 将阈值参数存入配置文件
    app.set_app_config_kv('demo_find_line', 'lmin', str(threshold[0]), False)  # 存储L的最小值
    app.set_app_config_kv('demo_find_line', 'lmax', str(threshold[1]), False)  # 存储L的最大值
    app.set_app_config_kv('demo_find_line', 'amin', str(threshold[2]), False)  # 存储a的最小值
    app.set_app_config_kv('demo_find_line', 'amax', str(threshold[3]), False)  # 存储a的最大值
    app.set_app_config_kv('demo_find_line', 'bmin', str(threshold[4]), False)  # 存储b的最小值
    app.set_app_config_kv('demo_find_line', 'bmax', str(threshold[5]), True)  # 存储b的最大值

def get_configured_threshold():
    '''
    从配置文件中获取存储的阈值参数
    '''
    threshold = [0, 100, -128, 127, -128, 127]  # 默认阈值

    # 从配置文件中读取阈值参数
    value_str = app.get_app_config_kv('demo_find_line', 'lmin', '', False)  # 读取L的最小值
    if len(value_str) > 0:
        threshold[0] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'lmax', '', False)  # 读取L的最大值
    if len(value_str) > 0:
        threshold[1] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'amin', '', False)  # 读取a的最小值
    if len(value_str) > 0:
        threshold[2] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'amax', '', False)  # 读取a的最大值
    if len(value_str) > 0:
        threshold[3] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'bmin', '', False)  # 读取b的最小值
    if len(value_str) > 0:
        threshold[4] = int(value_str)
    value_str = app.get_app_config_kv('demo_find_line', 'bmax', '', False)  # 读取b的最大值
    if len(value_str) > 0:
        threshold[5] = int(value_str)
    return threshold  # 返回读取的阈值

def btn_pressed(btn_id, state):
    '''
    按钮状态改变的回调函数
    '''
    global _to_show_binary, _to_get_pixel, _btn_id_binary, _btn_id_pixel  # 使用全局变量
    if state == 0:  # 只响应触摸抬起的动作
        return 

    # 根据按钮ID切换状态
    if btn_id == _btn_id_binary:  # 如果点击的是“二值化”按钮
        _to_show_binary = not _to_show_binary  # 切换二值化显示状态
        if _to_get_pixel:  # 如果当前处于取阈值模式
            _to_get_pixel = False  # 退出取阈值模式
    elif btn_id == _btn_id_pixel:  # 如果点击的是“取阈值”按钮
        _to_get_pixel = not _to_get_pixel  # 切换取阈值模式

def main():
    global _to_show_binary, _to_get_pixel, _btn_id_binary, _btn_id_pixel  # 使用全局变量

    print(app.get_app_config_path())  # 打印配置文件路径
    cam = camera.Camera(_image_width, _image_height)  # 初始化摄像头，设置分辨率为320x240
    gui = GUI()  # 初始化GUI

    # 创建“取阈值”按钮
    _btn_id_pixel = gui.createButton(0, _image_height - _btn_height, _btn_width, _btn_height)  # 创建按钮
    gui.setItemLabel(_btn_id_pixel, '取阈值')  # 设置按钮标签
    gui.setItemCallback(_btn_id_pixel, btn_pressed)  # 设置按钮回调函数

    # 创建“二值化”按钮
    _btn_id_binary = gui.createButton(_image_width - _btn_width, _image_height - _btn_height, _btn_width, _btn_height)  # 创建按钮
    gui.setItemLabel(_btn_id_binary, '二值化')  # 设置按钮标签
    gui.setItemCallback(_btn_id_binary, btn_pressed)  # 设置按钮回调函数

    last_x = -1  # 上一次触摸点的x坐标
    last_y = -1  # 上一次触摸点的y坐标
    threshold = get_configured_threshold()  # 获取配置文件中的阈值
    print(threshold)  # 打印阈值

    while not app.need_exit():  # 主循环，直到应用退出
        # 1. 读取图像
        img = cam.read()  # 从摄像头读取一帧图像
        if _to_show_binary:  # 如果处于二值化模式
            img = img.binary([threshold], False)  # 对图像进行二值化处理
        
        # 2. 图像取阈值
        if _to_get_pixel:  # 如果处于取阈值模式
            x, y = gui.get_touch()  # 获取触摸点坐标
            if last_x != x or last_y != y:  # 如果触摸点坐标发生变化
                last_x = x  # 更新上一次触摸点的x坐标
                last_y = y  # 更新上一次触摸点的y坐标

                # 获取触摸点的RGB值并转换为LAB值
                rgb = img.get_pixel(x, y, True)  # 获取触摸点的RGB值
                lab = rgb_to_lab(rgb)  # 将RGB值转换为LAB值
                if len(lab) >= 3:  # 如果LAB值有效
                    # 根据LAB值更新阈值
                    threshold[0] = math.floor(lab[0]) - 30  # 更新L的最小值
                    threshold[0] = threshold[0] if threshold[0] >= 0 else 0  # 确保L的最小值不小于0
                    threshold[1] = math.ceil(lab[0]) + 30  # 更新L的最大值
                    threshold[1] = threshold[1] if threshold[1] <= 100 else 100  # 确保L的最大值不大于100
                    threshold[2] = math.floor(lab[1]) - 10  # 更新a的最小值
                    threshold[2] = threshold[2] if threshold[2] >= -128 else -128  # 确保a的最小值不小于-128
                    threshold[3] = math.ceil(lab[1]) + 10  # 更新a的最大值
                    threshold[3] = threshold[3] if threshold[3] <= 127 else 127  # 确保a的最大值不大于127
                    threshold[4] = math.floor(lab[2]) - 10  # 更新b的最小值
                    threshold[4] = threshold[4] if threshold[4] >= -128 else -128  # 确保b的最小值不小于-128
                    threshold[5] = math.ceil(lab[2]) + 10  # 更新b的最大值
                    threshold[5] = threshold[5] if threshold[5] <= 127 else 127  # 确保b的最大值不大于127
                    print(threshold)  # 打印更新后的阈值
                    set_configured_threshold(threshold)  # 将新阈值存入配置文件
            img.draw_cross(x, y, image.COLOR_YELLOW, 8, 2)  # 在触摸点绘制十字标记
        
        # 3. 线性回归寻迹画线
        area_threshold = 100  # 定义区域阈值
        lines = img.get_regression([threshold], area_threshold=area_threshold, pixels_threshold=area_threshold)  # 获取检测到的线
        for line in lines:  # 遍历所有检测到的线
            img.draw_line(line.x1(), line.y1(), line.x2(), line.y2(), image.COLOR_GREEN, 2)  # 绘制线
            img.draw_string(0, 0, 'mag:{}  theta:{}  rho:{}'.format(line.magnitude(), line.theta(), line.rho()))  # 显示线的信息

        # 4. 更新显示
        gui.run(img)  # 更新GUI显示

if __name__ == '__main__':
    main()  # 程序入口