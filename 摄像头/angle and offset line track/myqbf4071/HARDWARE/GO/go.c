#include "go.h"



int data_sent_flag = 0;
float KP_ANGLE = 0.00050;
float KI_ANGLE = 0; // New Integral gain for the angle control
float KD_ANGLE = 0.037;
float ATarget=0.0f; // 电机A目标速度
float BTarget=0.0f; // 电机B目标速度
float base_speed = 0; // 基础速度offset
// 当前角度（从摄像头获取）
float current_angle = 0.0f;
float filtered_angle = 0.0f;
float alpha = 0.3f; // 滤波系数，可以根据实际情况调整
// 当前角度（从摄像头获取）
float current_offset = 0.0f;
float filtered_offset = 0.0f;
float alpha1 = 0.3f; // 滤波系数，可以根据实际情况调整
// 添加距离PID参数
float KP_OFFSET = -0.00011;  // 距离环P参数
float KI_OFFSET = 0;      // 距离环I参数
float KD_OFFSET = -0.053;  // 距离环D参数

// 设置舵机角度（0-180度）
void Set_Servo_Angle180(TIM_HandleTypeDef *htim, uint32_t Channel, float angle) {
    uint32_t pulse_width = 5 + (angle / 180.0f) * 20.0f;  // 将角度转换为PWM脉冲宽度
    __HAL_TIM_SET_COMPARE(htim, Channel, pulse_width);
}

// 设置舵机角度（0-270度）
void Set_Servo_Angle270(TIM_HandleTypeDef *htim, uint32_t Channel, float angle) {
    uint32_t pulse_width = 5 + (angle / 270.0f) * 20.0f;  // 将角度转换为PWM脉冲宽度
    __HAL_TIM_SET_COMPARE(htim, Channel, pulse_width);
}

// 优化PD控制器函数，分别处理角度和距离
float PID_Control_Angle(float error) {
    static float last_error = 0.0f;    
    static float integral = 0.0f;      
    
    integral = target_limit_float(integral + error, -100.0f, 100.0f);
    float derivative = error - last_error;
    float output = KP_ANGLE * error + KD_ANGLE * derivative + KI_ANGLE * integral;
    
    last_error = error;
    return output;
}

float PID_Control_Offset(float error) {
    static float last_error = 0.0f;    
    static float integral = 0.0f;      
    
    integral = target_limit_float(integral + error, -100.0f, 100.0f);
    float derivative = error - last_error;
    float output = KP_OFFSET * error + KD_OFFSET * derivative + KI_OFFSET * integral;
    
    last_error = error;
    return output;
}

// 限制PWM值的范围
void Limit_Pwm(int amplitude) {
    MOTOR_A.Motor_Pwm = target_limit_float(MOTOR_A.Motor_Pwm, -amplitude, amplitude);
    MOTOR_B.Motor_Pwm = target_limit_float(MOTOR_B.Motor_Pwm, -amplitude, amplitude);
}

// 限制浮点数的范围
float target_limit_float(float insert, float low, float high) {
    if (insert < low)
        return low;
    else if (insert > high)
        return high;
    else
        return insert;
}

// 限制整数的范围
int target_limit_int(int insert, int low, int high) {
    if (insert < low)
        return low;
    else if (insert > high)
        return high;
    else
        return insert;
}

// 增量式PI控制器（电机A）
int Incremental_PI_A(float Encoder, float Target) {
    static float Bias, Pwm, Last_bias;
    Bias = Target - Encoder; // 计算偏差
    Pwm += Velocity_KP * (Bias - Last_bias) + Velocity_KI * Bias; // 计算PWM值
    if (Pwm > 16700) Pwm = 16700;  // 限制PWM值
    if (Pwm < -16700) Pwm = -16700;
    Last_bias = Bias; // 保存上一次的偏差
    return Pwm;
}

// 增量式PI控制器（电机B）
int Incremental_PI_B(float Encoder, float Target) {
    static float Bias, Pwm, Last_bias;
    Bias = Target - Encoder; // 计算偏差
    Pwm += Velocity_KP * (Bias - Last_bias) + Velocity_KI * Bias; // 计算PWM值
    if (Pwm > 16700) Pwm = 16700;  // 限制PWM值
    if (Pwm < -16700) Pwm = -16700;
    Last_bias = Bias; // 保存上一次的偏差
    return Pwm;
}

static uint8_t rx_timeout = 0;

// 修改定时器中断处理函数
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
    if (htim->Instance == TIM7) {
        protocol_test_proc2();
        Get_Velocity_Form_Encoder();
        const float target_offset = 0.0;
        const float target_angle = 90.0f;
        float mapped_angle = Map_Angle(current_angle);
        float angle_error = mapped_angle - target_angle;
        
        // 计算距离误差（目标是使直线在图像中心）
        float offset_error = current_offset-target_offset;  // current_offset范围已经是-160到160

        // 分别计算角度和距离的PID输出
        float angle_output = PID_Control_Angle(angle_error);
        float offset_output = PID_Control_Offset(offset_error);
        
        // 将两个PID输出组合
        float steering = angle_output + offset_output;
        steering = target_limit_float(steering, -50.0f, 50.0f);
        
        // 更新电机目标速度（串级方式：基础速度受PID输出影响）
        float adjusted_base_speed = base_speed * (1.0f - fabsf(steering) / 50.0f);
        ATarget = target_limit_float(adjusted_base_speed - steering, -100.0f, 100.0f);
        BTarget = target_limit_float(adjusted_base_speed + steering, -100.0f, 100.0f);
        
        // 电机控制
        MOTOR_A.Motor_Pwm = Incremental_PI_A(MOTOR_BEncoder, ATarget);
        MOTOR_B.Motor_Pwm = Incremental_PI_B(MOTOR_CEncoder, BTarget);
        Limit_Pwm(16700);
        
        if (Car_Mode == Diff_Car) {
            Motor_Set(MOTOR_A.Motor_Pwm, MOTOR_B.Motor_Pwm);
        }
        
        static uint8_t data_sent_count = 0;
        if (++data_sent_count >= 10) {
            data_sent_flag = 1;
            data_sent_count = 0;
        }
    }
    else if (htim->Instance == TIM6) {
        static uint8_t hmi_count = 0;
        if (++hmi_count >=50) {  // 100ms
            HMI_Reaction();

            hmi_count = 0;
        }
        if (rx_timeout > 0) {
            rx_timeout--;
        }
    }
}

// 更新当前角度（从UART4接收数据）
void Update_Current_Angle(float angle) {
    filtered_angle = alpha * angle + (1 - alpha) * filtered_angle;  // 一阶低通滤波
    current_angle = filtered_angle;
}
void Update_Current_Offset(float offset) {
    filtered_offset = alpha1 * offset + (1 - alpha) * filtered_offset;  // 一阶低通滤波
    current_offset = filtered_offset;
}




// 角度映射函数
float Map_Angle(float original_angle) {
    float mapped_angle;

    if (original_angle >= 0 && original_angle <= 180) {
        // 右边（0到180），保持不变
        mapped_angle = original_angle;
    } else if (original_angle > 180 && original_angle <= 360) {
        // 左边（180到0），映射为0到180
        mapped_angle = 360 - original_angle;
    } else {
        // 非法角度，默认为90（中间值）
        mapped_angle = 90.0f;
    }

    return mapped_angle;
}








