#include "encoder.h"
// 左轮B编码器初始值
int OriginalEncoderB;  
// 左轮C编码器初始值
int OriginalEncoderC;  
// 左轮B轮速度，单位：m/s
float MOTOR_BEncoder;  
// 左轮C轮速度，单位：m/s
float MOTOR_CEncoder;  

/**************************************************************************
函数功能：读取左轮编码器
全局变量：TIMX - 定时器编号（3 或 4）
返回值：左轮编码器的值
备注：
  1. 该函数通过定时器计数器读取编码器值
  2. 支持定时器TIM3和TIM4，默认读取TIM3编码器的值
**************************************************************************/
int Read_Encoder(uint8_t TIMX)
{
    int Encoder_TIM;
    switch(TIMX)
    {
        case 3:
            Encoder_TIM = (short)TIM3->CNT;  // 读取 TIM3 编码器的值
            TIM3->CNT = 0;                  // 清空 TIM3 编码器计数器

            break;
        case 4:
            Encoder_TIM = (short)TIM4->CNT;  // 读取 TIM4 编码器的值
            TIM4->CNT = 0;                  // 清空 TIM4 编码器计数器

            break;
        default:
            Encoder_TIM = 0;  // 如果不是 TIM3 或 TIM4，返回0
    }
    return Encoder_TIM;
}

/**************************************************************************
函数功能：初始化编码器的参数
备注：
  1. 该函数用于初始化编码器的精度和轮子周长等参数
  2. 轮子周长会影响编码器转换后的速度值
**************************************************************************/
void Encoder_Init(void)
{
    // 初始化编码器精度：每转多少脉冲
    Encoder_precision = (float)(EncoderMultiples * Hall_13 * HALL_30F);

    // 初始化轮子周长：根据轮子的直径计算
    Wheel_perimeter = Black_WheelDiameter * PI;
}

/**************************************************************************
函数功能：根据编码器的值计算线速度，单位：m/s
备注：
  1. 该函数通过读取编码器值，计算轮子的线速度
  2. 左轮B的编码器值会被用来计算速度，右轮C同样计算
  3. 编码器的值会被存储在MOTOR_BEncoder和MOTOR_CEncoder中
**************************************************************************/
void Get_Velocity_Form_Encoder(void)
{
    float Encoder_B_pr, Encoder_C_pr;

    // 读取左轮B的编码器原始值
    OriginalEncoderB = Read_Encoder(3);  // 读取 TIM3 编码器的值
    OriginalEncoderC = Read_Encoder(4);  // 读取 TIM4 编码器的值

    // 转换为实际的编码器数值
    Encoder_B_pr = -OriginalEncoderB;  // 左轮B的编码器值
    Encoder_C_pr = OriginalEncoderC;   // 左轮C的编码器值

    // 计算编码器转换后的速度（单位：m/s）
    MOTOR_BEncoder = Encoder_B_pr * CONTROL_FREQUENCY * Wheel_perimeter / Encoder_precision;  
    MOTOR_CEncoder = Encoder_C_pr * CONTROL_FREQUENCY * Wheel_perimeter / Encoder_precision; 
}






