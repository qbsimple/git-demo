#ifndef __TJC_USART_HMI_H
#define __TJC_USART_HMI_H

#include "head.h"

/**
 * 发送HMI（人机界面）显示数据
 */



// 数据处理函数
void HMI_Process_Data(void);
void HMI_UART_IRQHandler(uint8_t data);

// 发送函数
void HMI_send_string(char* name, char* showdata);
void HMI_send_number(char* name, int num);
void HMI_send_float(char* name, float num);


// 初始化和处理函数
void HMI_Init(void);
void HMI_Reaction(void);







void tjc_send_string(char* str);
void tjc_send_txt(char* objname, char* attribute, char* txt);
void tjc_send_val(char* objname, char* attribute, int val);
void tjc_send_nstring(char* str, unsigned char str_length);




#define RINGBUFFER_LEN	(500)     

#define code_c() initRingBuffer()
#define udelete(x) deleteRingBuffer(x)
#define u(x) read1ByteFromRingBuffer(x)

extern uint8_t RxBuffer[1];
extern uint32_t msTicks;

// 添加环形缓冲区相关函数声明
void initRingBuffer(void);
void write1ByteToRingBuffer(uint8_t data);
void deleteRingBuffer(uint16_t size);
uint16_t getRingBufferLength(void);
uint8_t read1ByteFromRingBuffer(uint16_t position);
uint8_t isRingBufferOverflow(void);
void HMI_send_float10000(char* name, float num);









#endif


