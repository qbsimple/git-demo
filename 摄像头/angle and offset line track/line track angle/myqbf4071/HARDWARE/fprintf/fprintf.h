#ifndef __FPRINTF_H
#define __FPRINTF_H

#include "head.h"
#include <stdio.h>  // 引入标准输入输出库，用于 printf 和文件操作相关函数

// 外部声明 UART 句柄
extern UART_HandleTypeDef huart1;  // USART1 的句柄
extern UART_HandleTypeDef huart3;  // USART3 的句柄
extern UART_HandleTypeDef huart6;  // USART6 的句柄

// 外部声明自定义文件流指针
extern FILE *uart1_stream;  // 对应 USART1 的文件流
extern FILE *uart3_stream;  // 对应 USART3 的文件流
extern FILE *uart6_stream;  // 对应 USART6 的文件流

// 函数声明：初始化自定义流
void init_custom_streams(void);
// 函数声明：重定向 fputc 函数
int fputc(int ch, FILE *str);

#endif // __CUSTOM_UART_H
