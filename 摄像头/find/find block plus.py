
# from maix import camera, display, image, nn, app
# import sys
# sys.path.append('/root/exam')
# import servo

# # 初始化参数
# INIT_POS_X = 90  # 横向舵机初始位置（180度范围）
# INIT_POS_Y = 90  # 纵向舵机初始位置（270度范围）
# FILTER_FACTOR = 0.2  # 滤波系数
# KP_X = 0.15  # 横向比例系数
# KI_X = 0.0025  # 横向积分系数
# KP_Y = 0.15  # 纵向比例系数
# KI_Y = 0.0025  # 纵向积分系数

# # 加载模型和初始化摄像头
# # 加载模型和初始化摄像头
# detector = nn.Retinaface(model="/root/models/retinaface.mud")
# cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
# dis = display.Display()
# servo_x = servo.Servo180(6, INIT_POS_X)  # 横向舵机（180度）
# servo_y = servo.Servo180(7, INIT_POS_Y)  # 纵向舵机（270度）

# # 初始化变量
# target_x_pos = INIT_POS_X
# target_y_pos = INIT_POS_Y
# last_err_x_pos = 0
# last_err_y_pos = 0

# # 阈值参数

# image_width = detector.input_width()
# image_height = detector.input_height()
# def calculate_error(corners):
#     """计算横向和纵向误差"""
#     center_x = (corners[0][0] + corners[1][0] + corners[2][0] + corners[3][0]) / 4
#     center_y = (corners[0][1] + corners[1][1] + corners[2][1] + corners[3][1]) / 4
#     err_x_pos = 640 / 2 - center_x  # 横向误差
#     err_y_pos = 480 / 2 - center_y  # 纵向误差
#     return err_x_pos, err_y_pos

# def update_servo_position(err_x_pos, err_y_pos):
#     """更新舵机位置"""
#     global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

#     # 滤波处理
#     err_x_pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos
#     err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

#     # PID 控制（仅使用 PI）
#     delta_x_pos = KP_X * (err_x_pos - last_err_x_pos) + KI_X * err_x_pos
#     delta_y_pos = KP_Y * (err_y_pos - last_err_y_pos) + KI_Y * err_y_pos

#     last_err_x_pos = err_x_pos
#     last_err_y_pos = err_y_pos

#     target_x_pos += delta_x_pos
#     target_y_pos += delta_y_pos

#     # 限制舵机角度范围
#     target_x_pos = max(0, min(180, target_x_pos))  # x轴范围：0~180度
#     target_y_pos = max(0, min(180, target_y_pos))  # y轴范围：0~270度

#     # 控制舵机
#     servo_x.set_angle(int(target_x_pos))
#     servo_y.set_angle(int(target_y_pos))

# def draw_blob_rectangle(img, blob):
#     """绘制检测到的目标矩形框"""
#     corners = blob.corners()
#     for i in range(4):
#         img.draw_line(corners[i][0], corners[i][1], corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], image.COLOR_RED)

# def main_loop():
#     """主循环"""
#     global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

#     while not app.need_exit():
#         img = cam.read()

#         objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
#         if len(objs) == 0:  # 没有找到目标时，仅显示，不做追踪处理
#             dis.show(img)
#             continue

#         # 处理每个检测到的目标
#         for obj in objs:
#             obj = objs[0]
#             img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
#             # 计算横向舵机位置偏差，并进行一阶滞后滤波
#             err_x_pos = image_width / 2 - (obj.x + obj.w / 2)
#             err__pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos
#                     # 计算纵向舵机位置偏差，并进行一阶滞后滤波
#             err_y_pos = image_height / 2 - (obj.y + obj.h / 2)
#             err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos
#             update_servo_position(err_x_pos, err_y_pos)

#         # 显示图像
#         dis.show(img)

# if __name__ == "__main__":
#     try:
#         main_loop()
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         # 释放资源
#         cam.close()
#         dis.close()
#         servo_x.release()
#         servo_y.release()
# from maix import camera, display, image, nn, app
# import sys
# sys.path.append('/root/exam')
# import servo

# # 初始化参数
# INIT_POS_X = 90  # 横向舵机初始位置（180度范围）
# INIT_POS_Y = 90  # 纵向舵机初始位置（270度范围）
# FILTER_FACTOR = 0.3  # 滤波系数
# KP_X = 0.15  # 横向比例系数
# KI_X = 0.0025  # 横向积分系数
# KP_Y = 0.15  # 纵向比例系数
# KI_Y = 0.0025  # 纵向积分系数

# # 加载模型和初始化摄像头
# detector = nn.Retinaface(model="/root/models/retinaface.mud")
# cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
# dis = display.Display()
# servo_x = servo.Servo180(6, INIT_POS_X)  # 横向舵机（180度）
# servo_y = servo.Servo180(7, INIT_POS_Y)  # 纵向舵机（270度）

# # 初始化变量
# target_x_pos = INIT_POS_X
# target_y_pos = INIT_POS_Y
# last_err_x_pos = 0
# last_err_y_pos = 0

# # 图像尺寸
# image_width = detector.input_width()
# image_height = detector.input_height()

# def calculate_error(obj):
#     """计算目标中心与图像中心的误差"""
#     center_x = obj.x + obj.w / 2
#     center_y = obj.y + obj.h / 2
#     err_x_pos = image_width / 2 - center_x  # 横向误差
#     err_y_pos = image_height / 2 - center_y  # 纵向误差
#     return err_x_pos, err_y_pos

# def update_servo_position(err_x_pos, err_y_pos):
#     """更新舵机位置"""
#     global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

#     # 滤波处理
#     err_x_pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos
#     err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

#     # PID 控制（仅使用 PI）
#     delta_x_pos = KP_X * (err_x_pos - last_err_x_pos) + KI_X * err_x_pos
#     delta_y_pos = KP_Y * (err_y_pos - last_err_y_pos) + KI_Y * err_y_pos

#     last_err_x_pos = err_x_pos
#     last_err_y_pos = err_y_pos

#     target_x_pos += delta_x_pos
#     target_y_pos += delta_y_pos

#     # 限制舵机角度范围
#     target_x_pos = max(0, min(180, target_x_pos))  # x轴范围：0~180度
#     target_y_pos = max(0, min(180, target_y_pos))  # y轴范围：0~270度

#     # 控制舵机
#     servo_x.set_angle(int(target_x_pos))
#     servo_y.set_angle(int(target_y_pos))

# def draw_target_rectangle(img, obj):
#     """绘制检测到的目标矩形框"""
#     img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)

# def main_loop():
#     """主循环"""
#     global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

#     while not app.need_exit():
#         img = cam.read()

#         objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
#         if len(objs) == 0:  # 没有找到目标时，仅显示，不做追踪处理
#             dis.show(img)
#             continue

#         # 处理每个检测到的目标（默认追踪第一个目标）
#         obj = objs[0]
#         draw_target_rectangle(img, obj)

#         # 计算误差并更新舵机位置
#         err_x_pos, err_y_pos = calculate_error(obj)
#         update_servo_position(err_x_pos, err_y_pos)

#         # 显示图像
#         dis.show(img)

# if __name__ == "__main__":
#     try:
#         main_loop()
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         # 释放资源
#         cam.close()
#         dis.close()
#         servo_x.release()
#         servo_y.release()



from maix import camera, display, image, nn, app,pinmap
import sys
import time

# 添加自定义模块路径
sys.path.append('/root/exam')
import servo
pinmap.set_pin_function("B3", "GPIOB3")
led = gpio.GPIO("GPIOB3", gpio.Mode.OUT)
# 初始化参数
INIT_POS_X = 90  # 横向舵机初始位置（180度范围）
INIT_POS_Y = 90  # 纵向舵机初始位置（270度范围）
FILTER_FACTOR = 0.3  # 滤波系数
KP_X = 0.2  # 横向比例系数
KI_X = 0.003  # 横向积分系数
KP_Y = 0.2  # 纵向比例系数
KI_Y = 0.003  # 纵向积分系数

# 加载模型和初始化硬件
detector = nn.Retinaface(model="/root/models/retinaface.mud")  # 加载人脸检测模型
cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())  # 初始化摄像头
dis = display.Display()  # 初始化显示屏
servo_x = servo.Servo180(6, INIT_POS_X)  # 横向舵机（180度）
servo_y = servo.Servo180(7, INIT_POS_Y)  # 纵向舵机（270度）

# 初始化变量
target_x_pos = INIT_POS_X  # 目标横向角度
target_y_pos = INIT_POS_Y  # 目标纵向角度
last_err_x_pos = 0  # 上一次横向误差
last_err_y_pos = 0  # 上一次纵向误差

# 图像尺寸
image_width = detector.input_width()
image_height = detector.input_height()

def calculate_error(obj):
    """
    计算目标中心与图像中心的误差
    :param obj: 检测到的目标对象
    :return: 横向误差, 纵向误差
    """
    center_x = obj.x + obj.w / 2  # 目标中心X坐标
    center_y = obj.y + obj.h / 2  # 目标中心Y坐标
    err_x_pos = image_width / 2 - center_x  # 横向误差
    err_y_pos = image_height / 2 - center_y  # 纵向误差
    return err_x_pos, err_y_pos

def update_servo_position(err_x_pos, err_y_pos):
    """
    更新舵机位置
    :param err_x_pos: 横向误差
    :param err_y_pos: 纵向误差
    """
    global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

    # 滤波处理
    err_x_pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos
    err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

    # PID 控制（仅使用 PI）
    delta_x_pos = KP_X * (err_x_pos - last_err_x_pos) + KI_X * err_x_pos
    delta_y_pos = KP_Y * (err_y_pos - last_err_y_pos) + KI_Y * err_y_pos

    # 更新误差记录
    last_err_x_pos = err_x_pos
    last_err_y_pos = err_y_pos

    # 更新目标角度
    target_x_pos += delta_x_pos
    target_y_pos += delta_y_pos

    # 限制舵机角度范围
    target_x_pos = max(0, min(180, target_x_pos))  # x轴范围：0~180度
    target_y_pos = max(0, min(180, target_y_pos))  # y轴范围：0~270度

    # 控制舵机
    servo_x.set_angle(int(target_x_pos))
    servo_y.set_angle(int(target_y_pos))

def draw_target_rectangle(img, obj):
    """
    绘制检测到的目标矩形框
    :param img: 图像对象
    :param obj: 检测到的目标对象
    """
    img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)  # 绘制矩形框
    img.draw_string(obj.x, obj.y - 20, "Target", color=image.COLOR_GREEN)  # 绘制标签

def main_loop():
    """
    主循环：捕获图像、检测目标、更新舵机位置
    """
    global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

    while not app.need_exit():
        # 捕获图像
        img = cam.read()

        # 检测目标
        objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
        if len(objs) == 0:  # 没有找到目标时，仅显示图像
            dis.show(img)
            continue

        # 处理第一个检测到的目标
        obj = objs[0]
        draw_target_rectangle(img, obj)  # 绘制目标矩形框

        # 计算误差并更新舵机位置
        err_x_pos, err_y_pos = calculate_error(obj)
        update_servo_position(err_x_pos, err_y_pos)

        # 显示图像
        dis.show(img)



if __name__ == "__main__":
    try:
        main_loop()  # 启动主循环
    except Exception as e:
        print(f"An error occurred: {e}")  # 打印错误信息
    finally:
        # 释放资源
        cam.close()
        dis.close()
        servo_x.release()
        servo_y.release()