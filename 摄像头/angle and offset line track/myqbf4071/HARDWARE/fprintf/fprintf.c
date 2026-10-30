#include "fprintf.h"

// 定义自定义的 FILE 流变量，用于 UART 通信
FILE *uart1_stream;  // 用于 USART1
FILE *uart3_stream;  // 用于 USART3
FILE *uart6_stream;  // 用于 USART6

// 自定义 fputc 函数，用于通过指定的 UART 发送字符
int fputc(int ch, FILE *str)
{
    if (str == uart1_stream) {
        // 如果流是 uart1_stream（即 USART1），通过 USART1 发送字符
        HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, 0xFFFF);
    } else if (str == uart3_stream) {
        // 如果流是 uart3_stream（即 USART3），通过 USART3 发送字符
        HAL_UART_Transmit(&huart3, (uint8_t *)&ch, 1, 0xFFFF);
    } else if (str == uart6_stream) {
        // 如果流是 uart6_stream（即 USART6），通过 USART6 发送字符
        HAL_UART_Transmit(&huart6, (uint8_t *)&ch, 1, 0xFFFF);
    } else {
        // 默认情况下，通过 USART1 发送字符
        HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, 0xFFFF);
    }

    return ch;  // 返回发送的字符
}

// 初始化自定义流变量，将其指向相应的 UART 接口
void init_custom_streams(void)
{
    uart1_stream = (FILE *)1;  // 将 uart1_stream 指向 1，代表 USART1
    uart3_stream = (FILE *)3;  // 将 uart3_stream 指向 3，代表 USART3
    uart6_stream = (FILE *)6;  // 将 uart6_stream 指向 6，代表 USART6
}




