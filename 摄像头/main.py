# from maix import camera, display, image, nn, app
# import sys
# sys.path.append('/root/exam')
# import servo

# # 初始化参数
# INIT_POS_X = 90  # 横向舵机初始位置
# INIT_POS_Y = 100  # 纵向舵机初始位置
# FILTER_FACTOR = 0.15  # 滤波系数
# KP = 0.07  # 比例系数
# KI = 0  # 积分系数

# # 加载模型和初始化摄像头
# detector = nn.Retinaface(model="/root/models/retinaface.mud")
# cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
# dis = display.Display()

# # 初始化舵机
# servo_x = servo.Servo(6, INIT_POS_X)  # 横向舵机
# servo_y = servo.Servo(7, INIT_POS_Y)  # 纵向舵机

# # 初始化变量
# target_x_pos = INIT_POS_X
# target_y_pos = INIT_POS_Y
# last_err_x_pos = 0
# last_err_y_pos = 0
# image_width = detector.input_width()
# image_height = detector.input_height()

# while not app.need_exit():
#     img = cam.read()
#     objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
    
#     if len(objs) == 0:  # 没有找到人脸时，仅显示，不做追踪处理
#         dis.show(img)
#         continue
#     else:
#         obj = objs[0]
#         # 修改人脸框颜色为绿色
#         img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_GREEN)

#         # 计算横向误差（X 轴）
#         err_x_pos = image_width / 2 - (obj.x + obj.w / 2)
#         err_x_pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos

#         # PID 控制（仅使用 PI）
#         delta_x_pos = KP * (err_x_pos - last_err_x_pos) + KI * err_x_pos
#         last_err_x_pos = err_x_pos
#         target_x_pos += delta_x_pos

#         # 限制横向舵机角度范围
#         target_x_pos = max(0, min(180, target_x_pos))

#         # 控制横向舵机
#         servo_x.angle(int(target_x_pos))

#         # 计算纵向误差（Y 轴）
#         err_y_pos = image_height / 2 - (obj.y + obj.h / 2)
#         err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

#         # PID 控制（仅使用 PI）
#         delta_y_pos = KP * (err_y_pos - last_err_y_pos) + KI * err_y_pos
#         last_err_y_pos = err_y_pos
#         target_y_pos += delta_y_pos

#         # 限制纵向舵机角度范围
#         target_y_pos = max(0, min(180, target_y_pos))

#         # 控制纵向舵机
#         servo_y.angle(int(target_y_pos))

#         # 显示图像
#         dis.show(img)





# from maix import camera, display, image, nn, app
# import math
# import sys
# sys.path.append('/root/exam')
# import servo

# INIT_POS_X = 90
# INIT_POS_Y = 100
# FILTER_FACTOR = 0.15

# detector = nn.Retinaface(model="/root/models/retinaface.mud")
# cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
# dis = display.Display()

# servo_x = servo.Servo(7, INIT_POS_X)
# servo_y = servo.Servo(6, INIT_POS_Y)

# target_x_pos = INIT_POS_X
# target_y_pos = INIT_POS_Y

# last_err_x_pos = 0
# last_err_y_pos = 0

# image_width  = detector.input_width()
# image_height = detector.input_height()

# while not app.need_exit():
#     img = cam.read()
#     objs = detector.detect(img, conf_th = 0.4, iou_th = 0.45)
#     if len(objs) == 0: #没有找到人脸时，仅显示，不做追踪处理
#         dis.show(img)
#         continue
#     else:
#         obj = objs[0]
#         img.draw_rect(obj.x, obj.y, obj.w, obj.h, color = image.COLOR_RED)
#         # print('{}.{}.{}.{}'.format(obj.x, obj.y, obj.w, obj.h))

#         #取得横向舵机位置偏差，并进行一阶滞后滤波
#         err_x_pos = image_width/2 - (obj.x+obj.w/2)
#         err_x_pos = FILTER_FACTOR*err_x_pos + (1-FILTER_FACTOR)*last_err_x_pos

#         #增量PID 计算目标控制量(仅用到PI控制)
#         delta_x_pos = 0.2*(err_x_pos-last_err_x_pos) + 0*err_x_pos
#         last_err_x_pos = err_x_pos
#         target_x_pos += delta_x_pos
    
#         #取得纵向舵机位置偏差，并进行一阶滞后滤波
#         err_y_pos = image_height/2 - (obj.y+obj.h/2)
#         err_y_pos = FILTER_FACTOR*err_y_pos + (1-FILTER_FACTOR)*last_err_y_pos

#         #增量PID 计算目标控制量(仅用到PI控制)
#         delta_y_pos = 0.2*(err_y_pos-last_err_y_pos) + 0*err_y_pos
#         last_err_y_pos = err_y_pos
#         target_y_pos += delta_y_pos

#         #控制舵机角度
#         servo_x.angle(target_x_pos)
#         servo_y.angle(target_y_pos)

#         dis.show(img)













from maix import camera, display, image, nn, app
import sys
sys.path.append('/root/exam')
import servo

# 初始化参数
INIT_POS_X = 135  # 横向舵机初始位置（270度范围）
INIT_POS_Y = 135  # 纵向舵机初始位置（270度范围）
FILTER_FACTOR = 0.1  # 滤波系数
KP = -0.3  # 比例系数
KI = -0.001  # 积分系数

# 加载模型和初始化摄像头
detector = nn.Retinaface(model="/root/models/retinaface.mud")
cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
dis = display.Display()

# 初始化舵机
servo_x = servo.Servo270(6, INIT_POS_X)  # 横向舵机（270度）
servo_y = servo.Servo270(7, INIT_POS_Y)  # 纵向舵机（270度）

# 初始化变量
target_x_pos = INIT_POS_X
target_y_pos = INIT_POS_Y

last_err_x_pos = 0
last_err_y_pos = 0

image_width = detector.input_width()
image_height = detector.input_height()

while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th=0.4, iou_th=0.45)

    if len(objs) == 0:  # 没有找到人脸时，仅显示，不做追踪处理
        dis.show(img)
        continue
    else:
        obj = objs[0]
        img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)

        # 计算横向舵机位置偏差，并进行一阶滞后滤波
        err_x_pos = image_width / 2 - (obj.x + obj.w / 2)
        err_x_pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos

        # 增量PID 计算目标控制量（使用 PI 控制）
        delta_x_pos = KP * (err_x_pos - last_err_x_pos) + KI * err_x_pos
        last_err_x_pos = err_x_pos
        target_x_pos += delta_x_pos

        # 计算纵向舵机位置偏差，并进行一阶滞后滤波
        err_y_pos = image_height / 2 - (obj.y + obj.h / 2)
        err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

        # 增量PID 计算目标控制量（使用 PI 控制）
        delta_y_pos = KP * (err_y_pos - last_err_y_pos) + KI * err_y_pos
        last_err_y_pos = err_y_pos
        target_y_pos += delta_y_pos

        # 限制舵机角度范围
        target_x_pos = max(0, min(270, target_x_pos))  # x轴范围：0~270度
        target_y_pos = max(0, min(270, target_y_pos))  # y轴范围：0~270度

        # 控制舵机角度
        servo_x.set_angle(int(target_x_pos))
        servo_y.set_angle(int(target_y_pos))

        # 显示图像
        dis.show(img)