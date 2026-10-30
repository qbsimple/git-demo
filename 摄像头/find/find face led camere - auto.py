from maix import camera, display, image, nn, app, gpio, pinmap, time
import sys
sys.path.append('/root/exam')
import servo

# 初始化参数
INIT_POS_X = 90  # 横向舵机初始位置（180度范围）
INIT_POS_Y = 90  # 纵向舵机初始位置（180度范围）
FILTER_FACTOR = 0.4  # 滤波系数
KP_X = 0.1  # 横向比例系数
KI_X = 0.02  # 横向积分系数
KP_Y = 0.1  # 纵向比例系数
KI_Y = 0.02  # 纵向积分系数

# 调整死区策略 - 使用两个不同的死区
SERVO_DEADZONE = 5  # 舵机控制死区
LED_DEADZONE = 12   # 增大LED控制死区，使重合更容易判定

# 初始化LED
pinmap.set_pin_function("B3", "GPIOB3")
led = gpio.GPIO("GPIOB3", gpio.Mode.OUT)
led.value(0)  # 初始状态为关闭

# 添加中心点重合计时变量
center_match_start_time = 0
CENTER_MATCH_DURATION = 0.8  # 减少保持中心重合时间，使LED更容易亮起

# 添加LED闪烁相关变量
led_blink_state = False
last_blink_time = 0
BLINK_INTERVAL = 0.3  # LED闪烁间隔（秒）

# 添加LED强制关闭变量
force_led_off = False
force_off_start_time = 0
FORCE_OFF_DURATION = 0.5  # 减少强制关闭持续时间

# 加载模型和初始化摄像头
detector = nn.Retinaface(model="/root/models/retinaface.mud")
cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
dis = display.Display()
servo_x = servo.Servo180(6, INIT_POS_X)  # 横向舵机（180度）
servo_y = servo.Servo180(7, INIT_POS_Y)  # 纵向舵机（180度）

# 初始化变量
target_x_pos = INIT_POS_X
target_y_pos = INIT_POS_Y
last_err_x_pos = 0
last_err_y_pos = 0
face_lost_count = 0
MAX_FACE_LOST = 30  # 连续30帧未检测到人脸则回到初始位置

# 获取图像尺寸
image_width = detector.input_width()
image_height = detector.input_height()

def calculate_error(obj):
    """计算横向和纵向误差"""
    center_x = obj.x + obj.w / 2
    center_y = obj.y + obj.h / 2
    err_x_pos = image_width / 2 - center_x  # 横向误差
    err_y_pos = image_height / 2 - center_y  # 纵向误差
    return err_x_pos, err_y_pos

def update_servo_position(err_x_pos, err_y_pos):
    """更新舵机位置"""
    global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos

    # 滤波处理
    err_x_pos = FILTER_FACTOR * err_x_pos + (1 - FILTER_FACTOR) * last_err_x_pos
    err_y_pos = FILTER_FACTOR * err_y_pos + (1 - FILTER_FACTOR) * last_err_y_pos

    # 死区控制 - 误差太小时使用更精细的控制
    if abs(err_x_pos) < SERVO_DEADZONE:
        # 在死区内使用更小的调整步长
        delta_x_pos = err_x_pos * 0.02  # 更小的调整系数
    else:
        # PID 控制
        delta_x_pos = KP_X * (err_x_pos - last_err_x_pos) + KI_X * err_x_pos
    
    if abs(err_y_pos) < SERVO_DEADZONE:
        # 在死区内使用更小的调整步长
        delta_y_pos = err_y_pos * 0.02  # 更小的调整系数
    else:
        # PID 控制
        delta_y_pos = KP_Y * (err_y_pos - last_err_y_pos) + KI_Y * err_y_pos

    last_err_x_pos = err_x_pos
    last_err_y_pos = err_y_pos

    target_x_pos += delta_x_pos
    target_y_pos += delta_y_pos

    # 限制舵机角度范围
    target_x_pos = max(0, min(180, target_x_pos))  # x轴范围：0~180度
    target_y_pos = max(0, min(180, target_y_pos))  # y轴范围：0~180度

    # 控制舵机
    servo_x.set_angle(int(target_x_pos))
    servo_y.set_angle(int(target_y_pos))
def scan_for_face(servo, start_angle, end_angle, step):
    """扫描指定范围内的角度，寻找人脸"""
    global face_lost_count

    for angle in range(start_angle, end_angle, step):
        servo.set_angle(angle)
        time.sleep(0.1)  # 等待舵机稳定
        img = cam.read()
        objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
        if objs:  # 如果检测到人脸，停止扫描
            face_lost_count = 0  # 重置人脸丢失计数
            return objs
    return None


def return_to_center(objs):
    """逐渐回到中心位置并尝试寻找人脸"""
    global target_x_pos, target_y_pos, face_lost_count

    # 如果没有检测到人脸，开始扫描周围区域
    if not objs:
        # 横向扫描
        for angle in range(0, 180, 5):  # 从30度到160度，每次增加5度
            servo_x.set_angle(angle)
            time.sleep(0.1)  # 等待舵机稳定
            img = cam.read()
            objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
            if objs:  # 如果检测到人脸，停止扫描
                face_lost_count = 0  # 重置人脸丢失计数
                break

        # 如果没有找到人脸，继续纵向扫描
        if not objs:
            for angle in range(0, 150, 5):  # 从30度到160度，每次增加5度
                servo_y.set_angle(angle)
                time.sleep(0.1)  # 等待舵机稳定
                img = cam.read()
                objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
                if objs:  # 如果检测到人脸，停止扫描
                    face_lost_count = 0  # 重置人脸丢失计数
                    break

    # 如果仍然没有找到人脸，回到初始位置
    if not objs:
        servo_x.set_angle(INIT_POS_X)
        servo_y.set_angle(INIT_POS_Y)
        time.sleep(0.5)  # 等待舵机稳定
    # global target_x_pos, target_y_pos
    
    # # 计算回中心的步长
    # step_x = (INIT_POS_X - target_x_pos) * 0.1
    # step_y = (INIT_POS_Y - target_y_pos) * 0.1
    
    # target_x_pos += step_x
    # target_y_pos += step_y
    
    # # 控制舵机
    # servo_x.set_angle(int(target_x_pos))
    # servo_y.set_angle(int(target_y_pos))

def select_best_face(objs):
    """选择最佳人脸进行追踪（选择最大的人脸）"""
    if not objs:
        return None
    
    # 按人脸面积大小排序
    objs.sort(key=lambda obj: obj.w * obj.h, reverse=True)
    return objs[0]

def draw_face_info(img, obj):
    """在图像上绘制人脸信息"""
    # 绘制人脸框
    img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
    
    # 绘制人脸中心点（绿色）
    center_x = int(obj.x + obj.w / 2)
    center_y = int(obj.y + obj.h / 2)
    img.draw_circle(center_x, center_y, 5, color=image.COLOR_GREEN, thickness=2)
    
    # 绘制图像中心点（蓝色）
    img.draw_circle(image_width // 2, image_height // 2, 5, color=image.COLOR_BLUE, thickness=2)
    
    # 绘制连接线
    img.draw_line(center_x, center_y, image_width // 2, image_height // 2, 
                 color=image.COLOR_YELLOW)
    
    # 计算距离
    distance_x = abs(center_x - image_width // 2)
    distance_y = abs(center_y - image_height // 2)
    
    # 计算欧氏距离
    distance = (distance_x**2 + distance_y**2)**0.5
    
    # 检查中心点是否接近中点 - 使用欧氏距离判断
    is_near_center = distance < LED_DEADZONE
    
    # 计算重合程度（0-100%）
    max_distance = max(image_width, image_height) / 4  # 最大参考距离
    overlap_percent = max(0, 100 - (distance / max_distance * 100))
    
    # 在图像上显示距离和重合度信息
    img.draw_string(10, 30, f"Distance: {distance:.1f} px", color=image.COLOR_WHITE, scale=1)
    img.draw_string(10, 50, f"Overlap: {overlap_percent:.1f}%", color=image.COLOR_WHITE, scale=1)
    
    return is_near_center, distance

def update_led_blink():
    """更新LED闪烁状态"""
    global led_blink_state, last_blink_time
    
    current_time = time.time()
    
    # 检查是否需要切换闪烁状态
    if current_time - last_blink_time >= BLINK_INTERVAL:
        led_blink_state = not led_blink_state
        led.value(1 if led_blink_state else 0)
        last_blink_time = current_time
    
    return led_blink_state

def main_loop():
    """主循环"""
    global target_x_pos, target_y_pos, last_err_x_pos, last_err_y_pos, face_lost_count
    global center_match_start_time, force_led_off, force_off_start_time

    # 稳定性检测变量
    stability_counter = 0
    last_distance = 0
    
    # LED当前状态
    led_is_on = False
    
    # 添加LED保持亮起的计时器
    led_on_start_time = 0
    LED_MIN_ON_TIME = 0.2  # LED最短亮起时间（秒）
    
    # 添加拍照相关变量
    photo_taken = False
    photo_count = 0
    PHOTO_DELAY = 1.0  # 拍照间隔时间（秒）
    last_photo_time = 0

    while not app.need_exit():
        img = cam.read()

        objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
        
        # 绘制图像中心十字线
        img.draw_line(image_width // 2, 0, image_width // 2, image_height, 
                     color=image.COLOR_BLUE, thickness=1)
        img.draw_line(0, image_height // 2, image_width, image_height // 2, 
                     color=image.COLOR_BLUE, thickness=1)
        
        # 绘制LED控制区域指示圆（表示接近中点的范围）
        img.draw_circle(
            image_width // 2, 
            image_height // 2, 
            LED_DEADZONE, 
            color=image.COLOR_YELLOW, 
            thickness=1
        )
        
        # 获取当前时间
        current_time = time.time()
        
        # 检查是否需要解除强制关闭状态
        if force_led_off and current_time - force_off_start_time >= FORCE_OFF_DURATION:
            force_led_off = False
        
        # 检查LED是否应该保持亮起
        if led_is_on and current_time - led_on_start_time < LED_MIN_ON_TIME:
            # LED在最短亮起时间内，保持亮起状态
            img.draw_string(10, 10, "LED ON!", color=image.COLOR_GREEN, scale=1.5)
            img.draw_string(10, 70, "LED Status: ON (locked)", color=image.COLOR_WHITE, scale=1)
            dis.show(img)
            continue
        
        if len(objs) == 0:  # 没有找到目标时
            face_lost_count += 1
            if face_lost_count > MAX_FACE_LOST:
                return_to_center(objs)  # 一段时间未检测到人脸，逐渐回到中心位置
            
            # 重置中心点重合计时和稳定性计数
            center_match_start_time = 0
            stability_counter = 0
            
            # 如果LED不是锁定亮起状态，则进入闪烁模式
            if not (led_is_on and current_time - led_on_start_time < LED_MIN_ON_TIME):
                # 更新LED闪烁状态
                blink_state = update_led_blink()
                led_is_on = False  # 闪烁模式不算作LED亮起
                
                # 显示状态信息
                img.draw_string(10, 10, "No face detected", color=image.COLOR_RED, scale=1.5)
                img.draw_string(10, 70, f"LED Status: BLINKING", color=image.COLOR_YELLOW, scale=1)
            
            # 重置拍照标志
            photo_taken = False
            
            dis.show(img)
            continue
        
        # 检测到人脸，如果不是锁定亮起状态，则停止闪烁模式
        if not (led_is_on and current_time - led_on_start_time < LED_MIN_ON_TIME):
            # 重置人脸丢失计数
            face_lost_count = 0
            
            # 选择最佳人脸
            best_face = select_best_face(objs)
            
            # 绘制人脸信息并检查是否接近中点
            is_near_center, current_distance = draw_face_info(img, best_face)
            
            # 检查位置稳定性 - 放宽标准
            is_stable = abs(current_distance - last_distance) < 3  # 距离变化小于3像素视为稳定
            
            if is_stable:
                stability_counter += 1
                if stability_counter > 10:  # 限制最大值
                    stability_counter = 10
            else:
                stability_counter = max(0, stability_counter - 1)  # 缓慢减少稳定性计数
                # 只有当位置非常不稳定时才强制关闭LED
                if not is_near_center and led_is_on:
                    led.value(0)
                    led_is_on = False
                    force_led_off = True
                    force_off_start_time = current_time
            
            last_distance = current_distance
            
            # 处理LED控制逻辑
            if force_led_off:
                # 强制关闭状态，显示倒计时
                remaining_off = max(0, FORCE_OFF_DURATION - (current_time - force_off_start_time))
                img.draw_string(10, 10, f"LED locked off: {remaining_off:.1f}s", color=image.COLOR_RED, scale=1.5)
                led.value(0)
                led_is_on = False
                # 重置拍照标志
                photo_taken = False
            elif is_near_center and stability_counter >= 3:  # 降低稳定性要求
                if center_match_start_time == 0:
                    center_match_start_time = current_time
                elif current_time - center_match_start_time >= CENTER_MATCH_DURATION:
                    # 点亮LED
                    led.value(1)
                    led_is_on = True
                    led_on_start_time = current_time  # 记录LED亮起时间
                    img.draw_string(10, 10, "LED ON!", color=image.COLOR_GREEN, scale=1.5)
                    
                    # 当LED亮起时拍照（添加拍照间隔控制）
                    if not photo_taken or (current_time - last_photo_time >= PHOTO_DELAY):
                        # 保存图像
                        photo_path = f"/root/face_photo_{photo_count}.jpg"
                        img.save(photo_path)
                        photo_count += 1
                        photo_taken = True
                        last_photo_time = current_time
                        # 在图像上显示拍照信息
                        img.draw_string(10, 110, f"Photo saved: {photo_path}", color=image.COLOR_GREEN, scale=1)
                else:
                    # 在图像上显示剩余时间
                    remaining = max(0, CENTER_MATCH_DURATION - (current_time - center_match_start_time))
                    img.draw_string(10, 10, f"Hold center: {remaining:.1f}s", color=image.COLOR_WHITE, scale=1)
                    # 确保LED关闭
                    led.value(0)
                    led_is_on = False
                    # 重置拍照标志
                    photo_taken = False
            else:
                center_match_start_time = 0
                img.draw_string(10, 10, "Move face to center circle", color=image.COLOR_RED, scale=1)
                # 确保LED关闭
                led.value(0)
                led_is_on = False
                # 重置拍照标志
                photo_taken = False
            
            # 显示LED状态和稳定性信息
            img.draw_string(10, 70, f"LED Status: {'ON' if led_is_on else 'OFF'}", color=image.COLOR_WHITE, scale=1)
            img.draw_string(10, 90, f"Stability: {stability_counter}/3", color=image.COLOR_WHITE, scale=1)
            
            # 计算误差
            err_x_pos, err_y_pos = calculate_error(best_face)
            
            # 更新舵机位置
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
        # 不调用不存在的方法，直接设置舵机到初始位置
        try:
            servo_x.set_angle(INIT_POS_X)
            servo_y.set_angle(INIT_POS_Y)
        except:
            pass
        led.value(0)  # 确保退出时LED关闭