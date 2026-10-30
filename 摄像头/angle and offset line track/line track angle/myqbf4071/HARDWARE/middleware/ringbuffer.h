#ifndef RINGBUFFER_H__
#define RINGBUFFER_H__
#include <head.h>
#include <stdint.h>
#include <assert.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

/* 环形缓冲区结构体 */
struct rbuffer
{
    uint8_t *buffer_ptr;  // 指向缓冲区的指针
    /* 使用 {read,write}_index 的最高位作为镜像位。你可以将其视为缓冲区增加了一个虚拟镜像，
     * 指针指向正常缓冲区或镜像缓冲区。如果 write_index 和 read_index 的值相同，
     * 但位于不同的镜像中，则缓冲区已满。如果 write_index 和 read_index 的值相同且位于
     * 同一个镜像中，则缓冲区为空。环形缓冲区的 ASCII 图示如下：
     *
     *          mirror = 0                    mirror = 1
     * +---+---+---+---+---+---+---+|+~~~+~~~+~~~+~~~+~~~+~~~+~~~+
     * | 0 | 1 | 2 | 3 | 4 | 5 | 6 ||| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 满
     * +---+---+---+---+---+---+---+|+~~~+~~~+~~~+~~~+~~~+~~~+~~~+
     *  read_idx-^                   write_idx-^
     *
     * +---+---+---+---+---+---+---+|+~~~+~~~+~~~+~~~+~~~+~~~+~~~+
     * | 0 | 1 | 2 | 3 | 4 | 5 | 6 ||| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 空
     * +---+---+---+---+---+---+---+|+~~~+~~~+~~~+~~~+~~~+~~~+~~~+
     * read_idx-^ ^-write_idx
     */

    uint32_t read_mirror : 1;   // 读指针的镜像位
    uint32_t read_index : 31;   // 读指针的索引
    uint32_t write_mirror : 1;  // 写指针的镜像位
    uint32_t write_index : 31;  // 写指针的索引
    /* 由于我们使用索引的最高位作为镜像位，缓冲区大小应为有符号整数且只能为正数 */
    int32_t buffer_size;        // 缓冲区大小
};

typedef struct rbuffer rbuffer_t;  // 环形缓冲区类型定义

/* 环形缓冲区状态枚举 */
enum rbuffer_state
{
    RB_EMPTY,     // 缓冲区为空
    RB_FULL,      // 缓冲区已满
    RB_HALFFULL,  // 缓冲区半满（既不满也不空）
};

/** 返回缓冲区中剩余的空闲空间大小 */
#define rbuffer_space_len(rb) ((rb)->buffer_size - rbuffer_data_len(rb))


/* 环形缓冲区操作函数 */
void rbuffer_init(rbuffer_t *rb, uint8_t *pool, int32_t size);  // 初始化环形缓冲区
void rbuffer_reset(rbuffer_t *rb);  // 重置环形缓冲区
uint32_t rbuffer_put(rbuffer_t *rb, const uint8_t *ptr, uint32_t length);  // 向缓冲区写入数据
uint32_t rbuffer_put_force(rbuffer_t *rb, const uint8_t *ptr, uint32_t length);  // 强制写入数据（覆盖旧数据）
uint32_t rbuffer_putchar(rbuffer_t *rb, const uint8_t ch);  // 向缓冲区写入一个字符
uint32_t rbuffer_putchar_force(rbuffer_t *rb, const uint8_t ch);  // 强制写入一个字符（覆盖旧数据）
uint32_t rbuffer_del(rbuffer_t *rb, uint32_t length);  // 从缓冲区删除指定长度的数据
uint32_t rbuffer_get(rbuffer_t *rb, uint8_t *ptr, uint32_t length);  // 从缓冲区读取数据
uint32_t rbuffer_peek(rbuffer_t *rb, uint8_t *ptr, uint32_t length);  // 查看缓冲区中的数据（不移动读指针）
uint32_t rbuffer_getchar(rbuffer_t *rb, uint8_t *ch);  // 从缓冲区读取一个字符
uint32_t rbuffer_data_len(rbuffer_t *rb);  // 获取缓冲区中有效数据的长度
enum rbuffer_state rbuffer_status(rbuffer_t *rb);  // 获取缓冲区的状态


#ifdef __cplusplus
}
#endif

#endif
