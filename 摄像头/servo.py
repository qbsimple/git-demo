'''
    180度和270度3线航模伺服驱动
'''

from maix import pwm, pinmap

class Servo180():
    SERVO_FREQ = 50        # 50Hz 20ms
    SERVO_MIN_DUTY = 2.5   # 2.5% -> 0.5ms
    SERVO_MAX_DUTY = 12.5  # 12.5% -> 2.5ms

    SERVO_MAX_ANGLE = 180  # 180度

    def __init__(self, pwm_id: int, angle: int) -> None:
        # 限制角度范围
        angle = Servo180.SERVO_MAX_ANGLE if angle > Servo180.SERVO_MAX_ANGLE else angle
        angle = 0 if angle < 0 else angle

        # 设置PWM引脚
        if pwm_id == 7:
            pinmap.set_pin_function("A19", "PWM7")
        elif pwm_id == 6:
            pinmap.set_pin_function("A18", "PWM6")
        elif pwm_id == 5:
            pinmap.set_pin_function("A17", "PWM5")
        elif pwm_id == 4:
            pinmap.set_pin_function("A16", "PWM4")
        else:
            raise ValueError("Invalid PWM ID")

        # 初始化PWM
        self.pwm = pwm.PWM(pwm_id, freq=Servo180.SERVO_FREQ, duty=self._angle_to_duty(angle), enable=True)

    def __del__(self) -> None:
        self.pwm.disable()

    def _angle_to_duty(self, angle: int) -> float:
        '''
        将角度转换为占空比
        '''
        return (Servo180.SERVO_MAX_DUTY - Servo180.SERVO_MIN_DUTY) / Servo180.SERVO_MAX_ANGLE * angle + Servo180.SERVO_MIN_DUTY

    def set_angle(self, angle: int) -> None:
        '''
        设定角度
        '''
        angle = Servo180.SERVO_MAX_ANGLE if angle > Servo180.SERVO_MAX_ANGLE else angle
        angle = 0 if angle < 0 else angle

        duty = self._angle_to_duty(angle)
        self.pwm.duty(duty)


class Servo270():
    SERVO_FREQ = 50        # 50Hz 20ms
    SERVO_MIN_DUTY = 2.5   # 2.5% -> 0.5ms
    SERVO_MAX_DUTY = 12.5  # 12.5% -> 2.5ms

    SERVO_MAX_ANGLE = 270  # 270度

    def __init__(self, pwm_id: int, angle: int) -> None:
        # 限制角度范围
        angle = Servo270.SERVO_MAX_ANGLE if angle > Servo270.SERVO_MAX_ANGLE else angle
        angle = 0 if angle < 0 else angle

        # 设置PWM引脚
        if pwm_id == 7:
            pinmap.set_pin_function("A19", "PWM7")
        elif pwm_id == 6:
            pinmap.set_pin_function("A18", "PWM6")
        elif pwm_id == 5:
            pinmap.set_pin_function("A17", "PWM5")
        elif pwm_id == 4:
            pinmap.set_pin_function("A16", "PWM4")
        else:
            raise ValueError("Invalid PWM ID")

        # 初始化PWM
        self.pwm = pwm.PWM(pwm_id, freq=Servo270.SERVO_FREQ, duty=self._angle_to_duty(angle), enable=True)

    def __del__(self) -> None:
        self.pwm.disable()

    def _angle_to_duty(self, angle: int) -> float:
        '''
        将角度转换为占空比
        '''
        return (Servo270.SERVO_MAX_DUTY - Servo270.SERVO_MIN_DUTY) / Servo270.SERVO_MAX_ANGLE * angle + Servo270.SERVO_MIN_DUTY

    def set_angle(self, angle: int) -> None:
        '''
        设定角度
        '''
        angle = Servo270.SERVO_MAX_ANGLE if angle > Servo270.SERVO_MAX_ANGLE else angle
        angle = 0 if angle < 0 else angle

        duty = self._angle_to_duty(angle)
        self.pwm.duty(duty)

