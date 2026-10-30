#ifndef __myitqb_H
#define __myitqb_H

#include "head.h"
#define USART_REC_LEN  400   // 接收缓冲区长度



// 外部变量声明
extern uint8_t g_Usart2_ReceiveData;
extern uint8_t g_Usart6_ReceiveData;


extern float Motor1Speed;
extern float Motor2Speed;

extern float sp;

extern uint16_t USART_RX_STA;
extern uint8_t USART_RX_BUF[USART_REC_LEN];
extern float current_angle;
void protocol_test_init(void);
void protocol_test_proc1(void);
void protocol_test_proc2(void);

#endif




