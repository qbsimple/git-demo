#ifndef _GO_H
#define _GO_H

#include "head.h"

// 函数声明
int Incremental_PI_A(float Encoder, float Target);
int Incremental_PI_B(float Encoder, float Target);
float target_limit_float(float insert, float low, float high);
int target_limit_int(int insert, int low, int high);
void Limit_Pwm(int amplitude);
void Update_Current_Distance(float distance);
float Map_Angle(float original_angle);
// 外部变量声明
extern float ATarget; // 电机A目标速度
extern float BTarget; // 电机B目标速度
extern float current_distance; // 当前距离
void Update_Current_Angle(float angle);
extern float base_speed; // 基础速度
extern float KP_ANGLE;
extern float KI_ANGLE; // New Integral gain for the angle control
extern float KD_ANGLE;
// 当前角度（从摄像头获取）
extern float current_angle;





#endif


