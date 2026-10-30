#include "system.h"

// 定义差动驱动机器人的车轮间距（单位：米）
#define DIFF_WHEEL_SPACING 0.177f

// PID 控制器的增益参数，主要用于速度控制
float Velocity_KP = 300.0f; // 比例增益，控制误差的响应强度
float Velocity_KI = 300.0f; // 积分增益，用于消除静态误差
float Velocity_KD = 0.0f;   // 微分增益（如有需要可以启用），用于抑制过度响应

// 机器人类型变量
// 0 = Mec_Car（机械臂车）
// 1 = Omni_Car（全向车）
// 2 = Akm_Car（阿克曼车）
// 3 = Diff_Car（差动驱动车）
// 4 = FourWheel_Car（四轮车）
// 5 = Tank_Car（坦克车）
uint8_t Car_Mode = Diff_Car;  // 默认设置为差动驱动车

// 电机控制参数结构体，表示左电机和右电机
Motor_parameter MOTOR_A, MOTOR_B;

// 编码器和车轮的相关参数
float Encoder_precision;    // 编码器分辨率（例如，每圈脉冲数）
float Wheel_perimeter;     // 车轮周长（单位：米）
float Wheel_spacing = DIFF_WHEEL_SPACING; // 驱动轮之间的距离（单位：米）

// 其他类型机器人的附加参数（如需要的话可以使用）
float Wheelbase; // 前后轴之间的距离（单位：米），常用于四轮车或坦克车等









