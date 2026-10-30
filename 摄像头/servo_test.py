# # 导入所需的模块
# from maix import pwm, time, pinmap,app

# # 定义舵机控制相关的常量
# SERVO_FREQ = 50        # 舵机的工作频率为50Hz，即周期为20ms
# SERVO_MIN_DUTY = 2.5   # 舵机最小角度对应的占空比为2.5%（对应0.5ms脉冲宽度）
# SERVO_MAX_DUTY = 12.5  # 舵机最大角度对应的占空比为12.5%（对应2.5ms脉冲宽度）

# # 设置PWM通道和引脚映射
# pwm_id = 7  # 使用PWM通道7
# pinmap.set_pin_function("A19", "PWM7")  # 将引脚A19映射为PWM7功能

# # 定义一个函数，将角度转换为占空比
# def angle_to_duty(angle):
#     """
#     将角度（0-180度）转换为对应的占空比
#     公式：占空比 = (最大占空比 - 最小占空比) / 180 * 角度 + 最小占空比
#     """
#     return (SERVO_MAX_DUTY - SERVO_MIN_DUTY) / 180 * angle + SERVO_MIN_DUTY

# # 初始化PWM输出
# out = pwm.PWM(pwm_id, freq=SERVO_FREQ, duty=angle_to_duty(0), enable=True)
# # 参数说明：
# # - pwm_id: 使用的PWM通道（这里是7）
# # - freq: PWM信号的频率（这里是50Hz）
# # - duty: 初始占空比（设置为0度对应的占空比）
# # - enable: 启用PWM输出
# while not app.need_exit():
# # 控制舵机从0度旋转到180度
#     for i in range(180):  # 循环180次，每次增加1度
#         out.duty(angle_to_duty(i))  # 设置当前角度对应的占空比
#         print(i)  # 打印当前角度
#         time.sleep_ms(20)  # 每次改变角度后等待20ms，控制舵机旋转速度

#     for i in range(180):
#         out.duty(angle_to_duty(181 - i))
#         print(i)
#         time.sleep_ms(20)

# 导入所需的模块
from maix import pwm, time, pinmap, app

# 定义舵机控制相关的常量
SERVO_FREQ = 50        # 舵机的工作频率为50Hz，即周期为20ms
SERVO_MIN_DUTY = 2.5   # 舵机最小角度对应的占空比为2.5%（对应0.5ms脉冲宽度）
SERVO_MAX_DUTY = 12.5  # 舵机最大角度对应的占空比为12.5%（对应2.5ms脉冲宽度）

# 设置PWM通道和引脚映射
pwm_id = 7  # 使用PWM通道7
pinmap.set_pin_function("A19", "PWM7")  # 将引脚A19映射为PWM7功能

# 定义一个函数，将角度转换为占空比
def angle_to_duty(angle):
    """
    将角度（0-180度）转换为对应的占空比
    公式：占空比 = (最大占空比 - 最小占空比) / 180 * 角度 + 最小占空比
    """
    return (SERVO_MAX_DUTY - SERVO_MIN_DUTY) / 180 * angle + SERVO_MIN_DUTY

# 初始化PWM输出
out = pwm.PWM(pwm_id, freq=SERVO_FREQ, duty=angle_to_duty(0), enable=True)
# 参数说明：
# - pwm_id: 使用的PWM通道（这里是7）
# - freq: PWM信号的频率（这里是50Hz）
# - duty: 初始占空比（设置为0度对应的占空比）
# - enable: 启用PWM输出

# 主循环
while not app.need_exit():
    # 控制舵机从0度旋转到180度
    for angle in range(0, 181):  # 0到180度
        out.duty(angle_to_duty(angle))  # 设置当前角度对应的占空比
        print(f"Current Angle: {angle}")  # 打印当前角度
        time.sleep_ms(10)  # 每次改变角度后等待20ms，控制舵机旋转速度

    # 控制舵机从180度旋转回0度
    for angle in range(180, -1, -1):  # 180到0度
        out.duty(angle_to_duty(angle))  # 设置当前角度对应的占空比
        print(f"Current Angle: {angle}")  # 打印当前角度
        time.sleep_ms(10)  # 每次改变角度后等待20ms，控制舵机旋转速度