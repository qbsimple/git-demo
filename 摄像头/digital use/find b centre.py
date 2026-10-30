# from maix import camera, display, image, nn, app
# import sys
# sys.path.append('/root/exam')
# import servo

# # 初始化参数
# INIT_POS_X = 90  # 横向舵机初始位置
# INIT_POS_Y = 100  # 纵向舵机初始位置
# FILTER_FACTOR = 0.2  # 滤波系数
# KP = 0.07  # 比例系数
# KI =0.001   # 积分系数

# # 加载模型和初始化摄像头

# cam = camera.Camera(640, 480)
# dis = display.Display()
# servo_y = servo.Servo(7, INIT_POS_Y)  # 纵向舵机

# # 初始化变量
# target_x_pos = INIT_POS_X
# target_y_pos = INIT_POS_Y
# last_err_x_pos = 0
# last_err_y_pos = 0

# area_threshold = 1000
# pixels_threshold = 1000
# # thresholds = [[0, 80, 40, 80, 10, 80]]        # red
# thresholds = [[0, 80, -120, -10, 0, 30]]        # green
# # thresholds = [[0, 80, 30, 100, -120, -60]]    # blue

# while not app.need_exit():
#     img = cam.read()

#     blobs = img.find_blobs(thresholds, area_threshold = 1000, pixels_threshold = 1000)
#     if len(blobs) == 0:  # 没有找到人脸时，仅显示，不做追踪处理
#         dis.show(img)
#         continue
#     else:
#         # 修改人脸框颜色为绿色
#         for b in blobs:
#             corners = b.corners()
#             for i in range(4):
#                 img.draw_line(corners[i][0], corners[i][1], corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], image.COLOR_RED)

#         # 计算纵向误差（Y 轴）
#                 err_y_pos = 480 / 2 - (corners[i][1] + corners[(i + 1) % 4][1] / 2)
#                 err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

#         # PID 控制（仅使用 PI）
#                 delta_y_pos = KP * (err_y_pos - last_err_y_pos) + KI * err_y_pos
#                 last_err_y_pos = err_y_pos
#                 target_y_pos += delta_y_pos

#         # 限制纵向舵机角度范围
#         target_y_pos = max(0, min(180, target_y_pos))

#         # 控制纵向舵机
#         servo_y.angle(int(target_y_pos))

#         # 显示图像
#         dis.show(img)



from maix import camera, display, image, nn, app
import sys
sys.path.append('/root/exam')
import servo

# 初始化参数

INIT_POS_Y = 90  # 纵向舵机初始位置
FILTER_FACTOR = 0.05  # 滤波系数
KP = 0.2  # 比例系数
KI = 0.01  # 积分系数

# 加载模型和初始化摄像头
cam = camera.Camera(640, 480)
dis = display.Display()
servo_y = servo.Servo(7, INIT_POS_Y)  # 纵向舵机

# 初始化变量
target_y_pos = INIT_POS_Y
last_err_y_pos = 0

# 阈值参数
area_threshold = 1000
pixels_threshold = 1000
thresholds = [[0, 80, -120, -10, 0, 30]]  # green

def calculate_error(corners):
    """计算纵向误差（Y轴）"""
    center_y = (corners[0][1] + corners[1][1] + corners[2][1] + corners[3][1]) / 4
    err_y_pos = 480 / 2 - center_y
    return err_y_pos

def update_servo_position(err_y_pos):
    """更新舵机位置"""
    global target_y_pos, last_err_y_pos

    # 滤波处理
    err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

    # PID 控制（仅使用 PI）
    delta_y_pos = KP * (err_y_pos - last_err_y_pos) + KI * err_y_pos
    last_err_y_pos = err_y_pos
    target_y_pos += delta_y_pos

    # 限制纵向舵机角度范围
    target_y_pos = max(0, min(180, target_y_pos))

    # 控制纵向舵机
    servo_y.angle(int(target_y_pos))

def draw_blob_rectangle(img, blob):
    """绘制检测到的目标矩形框"""
    corners = blob.corners()
    for i in range(4):
        img.draw_line(corners[i][0], corners[i][1], corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], image.COLOR_RED)

def main_loop():
    """主循环"""
    global target_y_pos, last_err_y_pos

    while not app.need_exit():
        img = cam.read()

        blobs = img.find_blobs(thresholds, area_threshold=area_threshold, pixels_threshold=pixels_threshold)
        if len(blobs) == 0:  # 没有找到目标时，仅显示，不做追踪处理
            dis.show(img)
            continue

        # 处理每个检测到的目标
        for blob in blobs:
            draw_blob_rectangle(img, blob)
            err_y_pos = calculate_error(blob.corners())
            update_servo_position(err_y_pos)

        # 显示图像
        dis.show(img)

if __name__ == "__main__":
    try:
        main_loop()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # 释放资源
        cam.close()
        dis.close()
        servo_y.release()





