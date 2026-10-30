#include "myitqb.h"
#define USART_REC_LEN  400   // 将接收缓冲区从200增加到400

//多串口支持：

//UART2：用于接收传感器数据（如陀螺仪）。

//UART4：用于接收摄像头的角度数据。

//UART6：用于接收控制命令（如电机速度控制）
// 外部变量定义

uint8_t g_Usart2_ReceiveData;
uint8_t g_Usart6_ReceiveData;
uint8_t Usart6_String[50];

uint8_t rx_buf[2], Bluetooth_data;

uint8_t Fore, Back, Left, Right;

float Motor1Speed;
float Motor2Speed;
float sp = 1.0f;

// USART接收缓冲区
uint8_t USART_RX_BUF[USART_REC_LEN];
uint16_t USART_RX_STA = 0;

// 协议相关变量
static uint8_t _u8Data = 0x00;
static uint8_t _aBuffer[256] = {0x00};
static rbuffer_t rbProtocol;

// 电机速度控制命令处理
static void handle_motor_command(uint8_t cmd) {
    switch (cmd) {
        case 'A':
            Motor1Speed = 2000;
            Motor2Speed = 2000;
            break;
        case 'B':
            Motor1Speed = -2000;
            Motor2Speed = -2000;
            break;
        case 'C':
            Motor1Speed = 0;
            Motor2Speed = 0;
            break;
        case 'D':
            Motor1Speed = 0;
            Motor2Speed = 1000;
            break;
        case 'E':
            Motor1Speed = 1000;
            Motor2Speed = 0;
            break;
        case 'F':
            if (sp <= 2.5f) sp += 0.2f;
            break;
        case 'G':
            if (sp >= 0) sp -= 0.2f;
            break;
        default:
            break;
    }
}

// 协议测试初始化
void protocol_test_init(void) {
    if (HAL_UART_Receive_IT(&huart4, &_u8Data, 1) != HAL_OK) {
        Error_Handler();
    }
    rbuffer_init(&rbProtocol, _aBuffer, sizeof(_aBuffer));
}

// 协议测试处理函数
void protocol_test_proc2(void) {
    int32_t rc = -1;
    uint32_t redundant = 0x00;
    uint8_t buffer[128] = {0x00};
    uint8_t payload[32] = {0x00};
    float angle = 0.0f;
    float distance = 0.0f;

    uint32_t len = rbuffer_data_len(&rbProtocol);
    if (len == 0) return;

    len = (len <= sizeof(buffer)) ? len : sizeof(buffer);
    rbuffer_peek(&rbProtocol, buffer, len);

    rc = packet_is_valid(buffer, len, &redundant);
    if (redundant > 0) {
        rbuffer_del(&rbProtocol, redundant);
    }

    if (rc >= 0) {
        packet_decode(&buffer[redundant], len - redundant, payload, sizeof(payload));
        memcpy(&angle, &payload[0], 4);
        memcpy(&distance, &payload[4], 4);

        Update_Current_Angle(angle);

        uint32_t packet_len = packet_length(&buffer[redundant], len - redundant);
        rbuffer_del(&rbProtocol, packet_len);
    } else if ((rc == -3) || (rbuffer_status(&rbProtocol) == RB_FULL)) {
        rbuffer_del(&rbProtocol, len);
    }
}

// UART接收完成中断回调函数
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    uint8_t Res;  // 添加 Res 变量定义

    

    if(huart->Instance == USART3)
    {

        // 将接收到的数据写入环形缓冲区
        write1ByteToRingBuffer(RxBuffer[0]);
        
        // 打印当前环形缓冲区状态

        
        // 重新启动接收
        HAL_UART_Receive_DMA(&huart3, RxBuffer, 1);
    }
    
    else if (huart->Instance == USART2) {
        Res = huart->Instance->DR;
        jy61p_ReceiveData(g_Usart2_ReceiveData);
        
        if (HAL_UART_Receive_DMA(&huart2, &g_Usart2_ReceiveData, 1) != HAL_OK) {
            Error_Handler();
        }
    }
    else if (huart->Instance == UART4) {
        rbuffer_putchar(&rbProtocol, _u8Data);
        
        if (HAL_UART_Receive_IT(&huart4, &_u8Data, 1) != HAL_OK) {
            Error_Handler();
        }
    }
    else if (huart->Instance == USART6) {
        Res = huart->Instance->DR;
        handle_motor_command(g_Usart6_ReceiveData);
        
        if (HAL_UART_Receive_DMA(&huart6, &g_Usart6_ReceiveData, 1) != HAL_OK) {
            Error_Handler();
        }
    }
}



