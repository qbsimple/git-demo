#include "jy62.h"
#include "ringbuffer.h"

#define PACKET_HEADER 0x55       // 数据包头
#define PACKET_TYPE_ANGLE 0x53   // 角度数据类型
#define PACKET_TYPE_ACCEL 0x51   // 加速度数据类型
#define PACKET_TYPE_GYRO 0x52    // 陀螺仪数据类型
#define PACKET_LENGTH 11         // 数据包长度

// 定义状态机枚举
typedef enum {
    STATE_WAIT_HEADER,  // 等待包头
    STATE_WAIT_TYPE,    // 等待数据类型
    STATE_RECEIVE_DATA  // 接收数据
} RxState_t;

static uint8_t JY62_RxBuffer[PACKET_LENGTH];  // 接收数据缓冲区
static volatile RxState_t RxState = STATE_WAIT_HEADER;  // 当前状态
static uint8_t RxIndex = 0;  // 接收数据缓冲区索引

// 定义环形队列
static rbuffer_t rx_rb;
static uint8_t rx_rb_buffer[128];  // 环形队列缓冲区，大小为128字节

float pitch, roll, yaw;      // 角度数据
float gyrox, gyroy, gyroz;  // 陀螺仪数据
float aacx, aacy, aacz;     // 加速度数据

/**
 * @brief 计算校验和
 * @param data 数据缓冲区
 * @param length 数据长度
 * @return 校验和
 */
static uint8_t CalculateChecksum(uint8_t *data, uint8_t length) {
    uint16_t sum = 0;
    for (uint8_t i = 0; i < length; i++) {
        sum += data[i];
    }
    return sum;
}

/**
 * @brief 解析角度数据
 * @param data 数据缓冲区
 */
static void ParseAngleData(uint8_t *data) {
    roll = ((int16_t)((data[3] << 8) | data[2]) / 32768.0f * 180.0f);
    pitch = ((int16_t)((data[5] << 8) | data[4]) / 32768.0f * 180.0f);
    yaw = ((int16_t)((data[7] << 8) | data[6]) / 32768.0f * 180.0f);
}

/**
 * @brief 解析加速度数据
 * @param data 数据缓冲区
 */
static void ParseAccelData(uint8_t *data) {
    aacx = ((int16_t)((data[3] << 8) | data[2]) / 32768.0f * 16.0f);
    aacy = ((int16_t)((data[5] << 8) | data[4]) / 32768.0f * 16.0f);
    aacz = ((int16_t)((data[7] << 8) | data[6]) / 32768.0f * 16.0f);
}

/**
 * @brief 解析陀螺仪数据
 * @param data 数据缓冲区
 */
static void ParseGyroData(uint8_t *data) {
    gyrox = ((int16_t)((data[3] << 8) | data[2]) / 32768.0f * 2000.0f);
    gyroy = ((int16_t)((data[5] << 8) | data[4]) / 32768.0f * 2000.0f);
    gyroz = ((int16_t)((data[7] << 8) | data[6]) / 32768.0f * 2000.0f);
}

/**
 * @brief 初始化环形队列
 */
void jy62_init(void) {
    rbuffer_init(&rx_rb, rx_rb_buffer, sizeof(rx_rb_buffer));
}

/**
 * @brief 数据包处理函数
 * @param RxData 串口接收的数据
 */
void jy61p_ReceiveData(uint8_t RxData) {
    // 将接收到的数据放入环形队列
    rbuffer_put(&rx_rb, &RxData, 1);

    // 从环形队列中读取数据并进行处理
    uint8_t data;
    while (rbuffer_get(&rx_rb, &data, 1) == 1) {
        switch (RxState) {
            case STATE_WAIT_HEADER:
                if (data == PACKET_HEADER) {  // 检测到包头
                    JY62_RxBuffer[RxIndex++] = data;
                    RxState = STATE_WAIT_TYPE;  // 进入等待数据类型状态
                }
                break;

            case STATE_WAIT_TYPE:
                if (data == PACKET_TYPE_ANGLE || data == PACKET_TYPE_ACCEL || data == PACKET_TYPE_GYRO) {
                    JY62_RxBuffer[RxIndex++] = data;
                    RxState = STATE_RECEIVE_DATA;  // 进入接收数据状态
                } else {
                    RxState = STATE_WAIT_HEADER;  // 数据包类型错误，回到初始状态
                    RxIndex = 0;
                }
                break;

            case STATE_RECEIVE_DATA:
                JY62_RxBuffer[RxIndex++] = data;
                if (RxIndex == PACKET_LENGTH) {  // 接收完一个完整的数据包
                    uint8_t checksum = CalculateChecksum(JY62_RxBuffer, PACKET_LENGTH - 1);
                    if (checksum == JY62_RxBuffer[PACKET_LENGTH - 1]) {  // 校验成功
                        switch (JY62_RxBuffer[1]) {  // 根据数据类型解析数据
                            case PACKET_TYPE_ANGLE:
                                ParseAngleData(JY62_RxBuffer);
                                break;
                            case PACKET_TYPE_ACCEL:
                                ParseAccelData(JY62_RxBuffer);
                                break;
                            case PACKET_TYPE_GYRO:
                                ParseGyroData(JY62_RxBuffer);
                                break;
                            default:
                                break;  // 未知数据类型
                        }
                    } else {
                        // 校验失败，丢弃数据包
                    }
                    RxState = STATE_WAIT_HEADER;  // 回到初始状态
                    RxIndex = 0;
                }
                break;

            default:
                RxState = STATE_WAIT_HEADER;  // 未知状态，回到初始状态
                RxIndex = 0;
                break;
        }
    }
}






