
from maix import camera, display, image, nn, app
import sys
sys.path.append('/root/exam')
import servo

# 初始化参数
INIT_POS_X = 90  # 横向舵机初始位置（180度范围）
INIT_POS_Y = 90  # 纵向舵机初始位置（270度范围）
FILTER_FACTOR = 0.2  # 滤波系数
KP_X = 0.15  # 横向比例系数
KI_X = 0.0025  # 横向积分系数
KP_Y = 0.15  # 纵向比例系数
KI_Y = 0.0025  # 纵向积分系数

# 加载模型和初始化摄像头
cam = camera.Camera(640, 480)
dis = display.Display()
servo_x = servo.Servo180(6, INIT_POS_X)  # 横向舵机（180度）
servo_y = servo.Servo180(7, INIT_POS_Y)  # 纵向舵机（270度）

# 初始化变量
target_x_pos = INIT_POS_X
target_y_pos = INIT_POS_Y
last_err_x_pos = 0
last_err_y_pos = 0

# 阈值参数
area_threshold = 1000
pixels_threshold = 1000
thresholds = [[0, 80, -120, -10, 0, 30]]  # green

def calculate_error(corners):
    """计算横向和纵向误差"""
    center_x = (corners[0][0] + corners[1][0] + corners[2][0] + corners[3][0]) / 4
    center_y = (corners[0][1] + corners[1][1] + corners[2][1] + corners[3][1]) / 4
    err_x_pos = 640 / 2 - center_x  # 横向误差
    err_y_pos = 480 / 2 - center_y  # 纵向误差
    return err_x_pos, err_y_pos

def update_servo_position(err_x_pos, err_y_pos):
    """更新舵机位置"""
    global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

    # 滤波处理
    err_x_pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos
    err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

    # PID 控制（仅使用 PI）
    delta_x_pos = KP_X * (err_x_pos - last_err_x_pos) + KI_X * err_x_pos
    delta_y_pos = KP_Y * (err_y_pos - last_err_y_pos) + KI_Y * err_y_pos

    last_err_x_pos = err_x_pos
    last_err_y_pos = err_y_pos

    target_x_pos += delta_x_pos
    target_y_pos += delta_y_pos

    # 限制舵机角度范围
    target_x_pos = max(0, min(180, target_x_pos))  # x轴范围：0~180度
    target_y_pos = max(0, min(180, target_y_pos))  # y轴范围：0~270度

    # 控制舵机
    servo_x.set_angle(int(target_x_pos))
    servo_y.set_angle(int(target_y_pos))

def draw_blob_rectangle(img, blob):
    """绘制检测到的目标矩形框"""
    corners = blob.corners()
    for i in range(4):
        img.draw_line(corners[i][0], corners[i][1], corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], image.COLOR_RED)

def main_loop():
    """主循环"""
    global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

    while not app.need_exit():
        img = cam.read()

        blobs = img.find_blobs(thresholds, area_threshold=area_threshold, pixels_threshold=pixels_threshold)
        if len(blobs) == 0:  # 没有找到目标时，仅显示，不做追踪处理
            dis.show(img)
            continue

        # 处理每个检测到的目标
        for blob in blobs:
            draw_blob_rectangle(img, blob)
            err_x_pos, err_y_pos = calculate_error(blob.corners())
            update_servo_position(err_x_pos, err_y_pos)

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
        servo_x.release()
        servo_y.release()