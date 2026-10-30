#ifndef __SYSTEM_H
#define __SYSTEM_H

// 包含 STM32 F4 系列的 HAL 库和中断头文件
#include "stm32f4xx_it.h"
#include "stm32f4xx_hal.h"

// 包含自定义头文件，一般用于定义硬件相关的函数、结构等
#include "head.h"

// 车辆模式枚举类型定义，表示不同的车辆控制模式
typedef enum 
{
    Mec_Car = 0,    // 机械臂车（假设是一种带机械臂的机器人）
    Omni_Car,       // 全向车（支持全方位移动）
    Akm_Car,        // 阿克曼车（通常为汽车类型，前轮转向）
    Diff_Car,       // 差动驱动车（两轮驱动）
    FourWheel_Car,  // 四轮车（四个轮子，可能为独立驱动）
    Tank_Car         // 坦克车（履带驱动）
} CarMode;

// 电机控制相关参数的结构体定义
typedef struct  
{
    float Encoder;     // 通过编码器读取电机的实时速度
    float Motor_Pwm;   // 电机PWM值，用于控制电机的实时速度
    float Target;      // 控制电机的目标速度
    float Velocity_KP; // 速度控制PID参数：比例增益
    float Velocity_KI; // 速度控制PID参数：积分增益
    float Velocity_KD; // 速度控制PID参数：微分增益
} Motor_parameter;

/****** 以下是外部变量的声明，这些变量在其他源文件中定义，供其他文件使用 ******/
// 当前车辆的驱动模式（通过 Car_Mode 来控制）
extern uint8_t Car_Mode;

// MOTOR_A 和 MOTOR_B 结构体分别表示两个电机的控制参数
extern Motor_parameter MOTOR_A, MOTOR_B;

// PID 控制器的参数，用于控制电机速度
extern float Velocity_KP, Velocity_KI, Velocity_KD;

// 编码器的精度
extern float Encoder_precision;

// 车轮的周长（用于计算车速等）
extern float Wheel_perimeter;

// 车轮之间的间距（用于差动驱动模型）
extern float Wheel_spacing; 

/****** C 标准库的头文件（用于实现常用功能） ******/
#include <stdio.h>   // 输入输出相关函数
#include <stdint.h>  // 标准整数类型
#include <stdlib.h>  // 一些常用的库函数
#include <string.h>  // 字符串处理函数
#include <math.h>    // 数学运算函数
#include "stdarg.h"  // 支持可变参数的函数

#endif  // __SYSTEM_H











