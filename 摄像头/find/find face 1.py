
from maix import camera, display, image, nn, app
import sys
sys.path.append('/root/exam')
import servo

# 初始化参数
INIT_POS_X = 90  # 横向舵机初始位置（180度范围）
INIT_POS_Y = 90  # 纵向舵机初始位置（270度范围）
FILTER_FACTOR = 0.3  # 滤波系数
KP_X = 0.2  # 横向比例系数
KI_X = 0.003  # 横向积分系数
KP_Y = 0.2  # 纵向比例系数
KI_Y = 0.003# 纵向积分系数

# 加载模型和初始化摄像头
# 加载模型和初始化摄像头
detector = nn.Retinaface(model="/root/models/retinaface.mud")
cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
dis = display.Display()
servo_x = servo.Servo180(6, INIT_POS_X)  # 横向舵机（180度）
servo_y = servo.Servo180(7, INIT_POS_Y)  # 纵向舵机（270度）

# 初始化变量
target_x_pos = INIT_POS_X
target_y_pos = INIT_POS_Y
last_err_x_pos = 0
last_err_y_pos = 0

# 阈值参数

image_width = detector.input_width()
image_height = detector.input_height()
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

        objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
        if len(objs) == 0:  # 没有找到目标时，仅显示，不做追踪处理
            dis.show(img)
            continue

        # 处理每个检测到的目标
        for obj in objs:
            obj = objs[0]
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
            # 计算横向舵机位置偏差，并进行一阶滞后滤波
            err_x_pos = image_width / 2 - (obj.x + obj.w / 2)
            err__pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos
                    # 计算纵向舵机位置偏差，并进行一阶滞后滤波
            err_y_pos = image_height / 2 - (obj.y + obj.h / 2)
            err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos
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





