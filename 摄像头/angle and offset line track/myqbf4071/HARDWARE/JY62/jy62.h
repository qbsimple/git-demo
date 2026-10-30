#ifndef __JY62_H
#define __JY62_H

#include "head.h"
#include "ringbuffer.h"

void jy61p_ReceiveData(uint8_t RxData);
void jy62_init(void);  // 新增初始化函数

extern float pitch, roll, yaw;      // 姿态角：俯仰角、横滚角、偏航角
extern float gyrox, gyroy, gyroz;  // 陀螺仪传感器数据：x、y、z轴角速度
extern float aacx, aacy, aacz;     // 加速度计传感器数据：x、y、z轴加速度

#endif
