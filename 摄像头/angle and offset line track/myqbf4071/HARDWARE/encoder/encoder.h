#ifndef __ENCODER_H
#define __ENCODER_H
#include "head.h"
// 控制频率，单位：Hz
#define CONTROL_FREQUENCY 100  

// 黑色轮子直径，单位：米
#define Black_WheelDiameter 0.065f  

// 编码器计数倍数，用于计算每转的编码器值
#define EncoderMultiples 4  

// 霍尔传感器每圈的脉冲数
#define Hall_13 13  

// 圆周率，用于计算轮子周长
#define PI 3.14159265f  

// 编码器的脉冲数，用于速度计算
#define HALL_30F 21 

void Encoder_Init(void);
int Read_Encoder(uint8_t TIMX);
void Get_Velocity_Form_Encoder(void);

// 左轮B编码器初始值
extern int OriginalEncoderB;  
// 左轮C编码器初始值
extern int OriginalEncoderC;  

// 左轮B轮速度，单位：m/s
extern float MOTOR_BEncoder;  
// 左轮C轮速度，单位：m/s
extern float MOTOR_CEncoder;

  
#endif
