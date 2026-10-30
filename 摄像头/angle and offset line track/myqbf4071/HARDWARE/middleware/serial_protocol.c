#include "serial_protocol.h"
#include <stdio.h>
#include <string.h>

/*
 * 协议帧格式：
 * 帧头(0xAA) + 协议数据长度(2字节) + 协议数据(可变长度) + 校验和(1字节) + 帧尾(0x55)
 */

#define HEAD 0xAA  // 帧头
#define TAIL 0x55  // 帧尾

/*
 * 计算校验和
 * 参数: data - 数据指针, len - 数据长度
 * 返回值: 计算得到的校验和
 */
static uint8_t check_sum(uint8_t* data, uint32_t len)
{
    uint8_t check_sum = 0x00;
    
    for(uint32_t i = 0; i < len; i++){
        check_sum += data[i];
    }
    
    return check_sum;
}

/*
 * 检查协议帧是否有效
 * 参数: data - 数据指针, len - 数据长度, redundant - 冗余字节数
 * 返回值: -1 -- 参数错误, -2 -- 长度不匹配, -3 -- 校验和错误
 */
int32_t packet_is_valid(uint8_t* data, uint32_t len, uint32_t* redundant)
{
    if((data == NULL) || (len == 0) || (redundant == NULL)){
        return -1;
    }
    
    uint32_t index = 0;
    for(index = 0; index < len; index++){
        if(data[index] != HEAD){
            index++;
        }
        else{
            break;
        }
    }
    *redundant = index;
    
    if((len-index) < 3){
        return -2;
    }
    
    uint16_t payload_len = 0x00;
    memcpy(&payload_len, &data[index+1], 2);
    if((len - index) < (payload_len + 5)){
        return -2;
    }
    
    if((data[index+3+payload_len+1] != TAIL) || 
       (check_sum(&data[index+1], 2+payload_len) != data[index+3+payload_len]))
    {
        return -3;
    }
    
    return 0;
}

/*
 * 获取协议帧的长度
 * 参数: data - 数据指针, len - 数据长度
 * 返回值: 协议帧的长度，如果数据无效则返回0
 */
uint32_t packet_length(uint8_t* data, uint32_t len)
{
    if((data == NULL) || (data[0] != HEAD) || (len < 5)){
        return 0;
    }
    
    uint16_t payload_len = 0;
    memcpy(&payload_len, &data[1], 2);
    
    return (3+payload_len+2);
}

/*
 * 编码协议帧
 * 参数: payload - 有效载荷数据, len - 有效载荷长度, packet_buff - 协议帧缓冲区, buff_len - 缓冲区长度
 * 返回值: 编码后的协议帧长度，如果参数错误则返回-1
 */
int32_t packet_encode(uint8_t* payload, uint32_t len, uint8_t* packet_buff, uint32_t buff_len)
{
    if((payload == NULL) || (packet_buff == NULL) || ((len + 5) > buff_len)){
        return -1;
    }
    
    uint16_t payload_len = len;
    uint32_t index = 0;
    
    packet_buff[index++] = HEAD;
    memcpy(&packet_buff[index], &payload_len, 2);
    index += 2;
    
    memcpy(&packet_buff[index], payload, len);
    index += len;
    
    uint8_t check = check_sum(&packet_buff[1], 2+len);
    packet_buff[index++] = check;
    packet_buff[index++] = TAIL;
    
    return index;
}

/*
 * 解码协议帧
 * 参数: data - 数据指针, len - 数据长度, payload_buff - 有效载荷缓冲区, buff_len - 缓冲区长度
 * 返回值: 解码后的有效载荷长度，如果参数错误则返回-1
 */
int32_t packet_decode(uint8_t* data, uint32_t len, uint8_t* payload_buff, uint32_t buff_len)
{
    if((data == NULL) || (data[0] != HEAD) || (len < 5) || (payload_buff == NULL)){
        return -1;
    }
    uint16_t payload_len = 0x00;
    memcpy(&payload_len, &data[1], 2);
    if((len < (payload_len+5)) || (buff_len < payload_len)){
        return -1;
    }
    
    memcpy(payload_buff, &data[3], payload_len);
    return payload_len;
}
