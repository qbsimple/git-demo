#include "tjc_usart_hmi.h"

// 在文件开头添加调试标志
#define DEBUG_UART_RECEIVE 1

#define FRAME_LENGTH 6   // 帧长度：帧头(1) + 命令(1) + 数据(2) + 帧尾(3)

typedef struct
{
    uint16_t Head;
    uint16_t Tail;
    uint16_t Length;
    uint8_t  Ring_data[RINGBUFFER_LEN];
}RingBuffer_t;

RingBuffer_t ringBuffer;
uint8_t RxBuffer[1];

// 命令定义，指令的值代表不同的操作
#define CMD_INCREASE_ATARGET      0x31   // 增加 ATarget
#define CMD_DECREASE_ATARGET      0x32   // 减少 ATarget
#define CMD_INCREASE_BTARGET      0x33   // 增加 BTarget
#define CMD_DECREASE_BTARGET      0x34   // 减少 BTarget
#define CMD_INCREASE_VELOCITY_KP  0x40   // 增加 Velocity_KP
#define CMD_DECREASE_VELOCITY_KP  0x41   // 减少 Velocity_KP
#define CMD_INCREASE_VELOCITY_KI  0x42   // 增加 Velocity_KI
#define CMD_DECREASE_VELOCITY_KI  0x43   // 减少 Velocity_KI
#define CMD_INCREASE_VELOCITY_KD  0x44   // 增加 Velocity_KD
#define CMD_DECREASE_VELOCITY_KD  0x45   // 减少 Velocity_KD
#define CMD_INCREASE_KP_ANGLE     0x50   // 增加 KP_ANGLE
#define CMD_DECREASE_KP_ANGLE     0x51   // 减少 KP_ANGLE
#define CMD_INCREASE_KI_ANGLE     0x52   // 增加 KI_ANGLE
#define CMD_DECREASE_KI_ANGLE     0x53   // 减少 KI_ANGLE
#define CMD_INCREASE_KD_ANGLE     0x54   // 增加 KD_ANGLE
#define CMD_DECREASE_KD_ANGLE     0x56   // 减少 KD_ANGLE
// 发送字符串到HMI界面
void HMI_send_string(char* name, char* showdata)
{
    // 向HMI发送字符串数据，格式为 name="showdata" 后面跟着结尾标志
    // 这里使用了 uart3_stream 输出，具体实现依赖于硬件
    fprintf(uart3_stream, "%s=\"%s\"\xff\xff\xff", name, showdata);
}

// 发送整数到HMI界面
void HMI_send_number(char* name, int num)
{
    // 向HMI发送整数数据，格式为 name=num 后面跟着结尾标志
    fprintf(uart3_stream, "%s=%d\xff\xff\xff", name, num);
}

// 发送浮点数到HMI界面
void HMI_send_float(char* name, float num)
{
    // 将浮点数乘以100并转换为整数，发送数据到HMI
    // 这样做是为了提高精度，避免浮点数表示问题
    fprintf(uart3_stream, "%s=%d\xff\xff\xff", name, (int)(num * 100));    
}
void HMI_send_float10000(char* name, float num)
{
    // 将浮点数乘以100并转换为整数，发送数据到HMI
    // 这样做是为了提高精度，避免浮点数表示问题
    fprintf(uart3_stream, "%s=%d\xff\xff\xff", name, (int)(num * 100000));    
}
// HMI初始化函数，初始化HMI显示值
void HMI_Init(void)
{
    printf("Starting HMI initialization...\r\n");
    
    // 初始化环形缓冲区
    initRingBuffer();
    printf("Ring buffer initialized\r\n");
    
    // 确保串口3已经初始化
    HAL_UART_DeInit(&huart3);
    HAL_UART_Init(&huart3);
    printf("UART3 reinitialized\r\n");
    
    // 清空接收缓冲区
    memset(RxBuffer, 0, sizeof(RxBuffer));
    
    // 启动串口接收中断
    if(HAL_UART_Receive_IT(&huart3, RxBuffer, 1) != HAL_OK)
    {
        printf("Failed to start UART receive, retrying...\r\n");
        // 如果启动失败，重试一次
        HAL_UART_AbortReceive_IT(&huart3);
        HAL_UART_Receive_IT(&huart3, RxBuffer, 1);
    }
    else
    {
        printf("UART receive started successfully\r\n");
    }
    
    // 发送初始化完成标志
    uint8_t init_data[] = "UART Init OK\r\n";
    HAL_UART_Transmit(&huart3, init_data, sizeof(init_data)-1, 0xFFFF);
    printf("Initialization complete\r\n");
    
    // 向HMI界面发送初始的浮动数据
    HMI_send_float("x0.val", base_speed);
//    HMI_send_float("x1.val", current_angle);
    HMI_send_float("x10.val", Velocity_KP);    
    HMI_send_float("x11.val", Velocity_KI);
    HMI_send_float("x12.val", Velocity_KD);
    HMI_send_float10000("x30.val", KP_ANGLE);    
    HMI_send_float10000("x31.val", KI_ANGLE);
    HMI_send_float10000("x32.val", KD_ANGLE);
}

void HMI_Reaction(void)
{
    uint16_t length;
    length = getRingBufferLength();
    
    while (length >= 3)  // 修改为3字节，因为实际收到的帧是3字节：0x55 CMD 0xFF
    {
        // 检查帧头和帧尾
        if (read1ByteFromRingBuffer(0) == 0x55 && read1ByteFromRingBuffer(2) == 0xFF)
        {
            uint8_t cmd = read1ByteFromRingBuffer(1);
            
            // 处理命令
            switch(cmd)
            {
                case CMD_INCREASE_ATARGET:  // 0x31
                    base_speed += 0.1f;
                    HMI_send_float("x0.val", base_speed);
                    break;
                    
                case CMD_DECREASE_ATARGET:  // 0x32
                    base_speed -= 0.1f;
                    HMI_send_float("x0.val", base_speed);
                    break;
                case CMD_INCREASE_VELOCITY_KP:  // 0x40
                    Velocity_KP += 50;
                    HMI_send_float("x10.val", Velocity_KP);
                    break;
                case CMD_DECREASE_VELOCITY_KP:  // 0x41
                    Velocity_KP -= 50;
                    HMI_send_float("x10.val", Velocity_KP);
                    break;
                case CMD_INCREASE_VELOCITY_KI:  // 0x42
                    Velocity_KI += 50;
                    HMI_send_float("x11.val", Velocity_KI);
                    break;
                case CMD_DECREASE_VELOCITY_KI:  // 0x43
                    Velocity_KI -= 50;
                    HMI_send_float("x11.val", Velocity_KI);
                    break;
                case CMD_INCREASE_VELOCITY_KD:  // 0x44
                    Velocity_KD += 50;
                    HMI_send_float("x12.val", Velocity_KD);
                    break;
                case CMD_DECREASE_VELOCITY_KD:  // 0x45
                    Velocity_KD -= 50;
                    HMI_send_float("x12.val", Velocity_KD);
                    break;
                case CMD_INCREASE_KP_ANGLE:  // 0x50
                    KP_ANGLE += 0.00002f;
                    HMI_send_float10000("x30.val", KP_ANGLE);
                    break;
                case CMD_DECREASE_KP_ANGLE:  // 0x51
                    KP_ANGLE -= 0.00002f;
                    HMI_send_float10000("x30.val", KP_ANGLE);
                    break;
                case CMD_INCREASE_KI_ANGLE:  // 0x52
                    KI_ANGLE += 0.000002f;
                    HMI_send_float10000("x31.val", KI_ANGLE);
                    break;
                case CMD_DECREASE_KI_ANGLE:  // 0x53
                    KI_ANGLE -= 0.000002f;
                    HMI_send_float10000("x31.val", KI_ANGLE);
                    break;
                case CMD_INCREASE_KD_ANGLE:  // 0x54
                    KD_ANGLE += 0.002f;
                    HMI_send_float10000("x32.val", KD_ANGLE);
                    break;
                case CMD_DECREASE_KD_ANGLE:  // 0x56
                    KD_ANGLE -= 0.002f;
                    HMI_send_float10000("x32.val", KD_ANGLE);
                    break;
                default:
                    break;
            }
            
            // 删除这一帧数据
            deleteRingBuffer(3);
        }
        else
        {
            // 如果帧头不对，删除一个字节继续查找
            deleteRingBuffer(1);
        }
        
        length = getRingBufferLength();
    }
    
    // 更新显示
    HMI_send_float("x0.val", base_speed);
    HMI_send_float("x10.val", Velocity_KP);    
    HMI_send_float("x11.val", Velocity_KI);
    HMI_send_float("x12.val", Velocity_KD);
    HMI_send_float10000("x30.val", KP_ANGLE);    
    HMI_send_float10000("x31.val", KI_ANGLE);
    HMI_send_float10000("x32.val", KD_ANGLE);
}

/********************************************************
º¯ÊýÃû£º  		intToStr
ÈÕÆÚ£º    	2024.09.18
¹¦ÄÜ£º    	½«ÕûÐÎ×ª»»Îª×Ö·û´®
ÊäÈë²ÎÊý£º		Òª×ª»»µÄÕûÐÎÊý¾Ý,Êä³öµÄ×Ö·û´®Êý×é
·µ»ØÖµ£º 		ÎÞ
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void intToStr(int num, char* str) {
    int i = 0;
    int isNegative = 0;

    // ´¦Àí¸ºÊý
    if (num < 0) {
        isNegative = 1;
        num = -num;
    }

    // ÌáÈ¡Ã¿Ò»Î»Êý×Ö
    do {
        str[i++] = (num % 10) + '0';
        num /= 10;
    } while (num);

    // Èç¹ûÊÇ¸ºÊý£¬Ìí¼Ó¸ººÅ
    if (isNegative) {
        str[i++] = '-';
    }

    // Ìí¼Ó×Ö·û´®ÖÕÖ¹·û
    str[i] = '\0';

    // ·´×ª×Ö·û´®
    int start = 0;
    int end = i - 1;
    while (start < end) {
        char temp = str[start];
        str[start] = str[end];
        str[end] = temp;
        start++;
        end--;
    }
    return ;
}

/********************************************************
º¯ÊýÃû£º  		uart_send_char
ÈÕÆÚ£º    	2024.09.18
¹¦ÄÜ£º    	´®¿Ú·¢ËÍµ¥¸ö×Ö·û
ÊäÈë²ÎÊý£º		Òª·¢ËÍµÄµ¥¸ö×Ö·û
·µ»ØÖµ£º 		ÎÞ
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void uart_send_char(char ch)
{
    uint8_t ch2 = (uint8_t)ch;
    // 等待上一次发送完成
    while(__HAL_UART_GET_FLAG(&huart3, UART_FLAG_TXE) == RESET);
    // 发送单个字符
    HAL_UART_Transmit_IT(&huart3, &ch2, 1);
    return;
}

void uart_send_string(char* str)
{
    //µ±Ç°×Ö·û´®µØÖ·²»ÔÚ½áÎ² ²¢ÇÒ ×Ö·û´®Ê×µØÖ·²»Îª¿Õ
    while(*str!=0&&str!=0)
    {
        //·¢ËÍ×Ö·û´®Ê×µØÖ·ÖÐµÄ×Ö·û£¬²¢ÇÒÔÚ·¢ËÍÍê³ÉÖ®ºóÊ×µØÖ·×ÔÔö
        uart_send_char(*str++);
    }
	return;
}

/********************************************************
º¯ÊýÃû£º  		tjc_send_string
ÈÕÆÚ£º    	2024.09.18
¹¦ÄÜ£º    	´®¿Ú·¢ËÍ×Ö·û´®ºÍ½áÊø·û
ÊäÈë²ÎÊý£º		Òª·¢ËÍµÄ×Ö·û´®
·µ»ØÖµ£º 		ÎÞ
Ê¾Àý:			tjc_send_val("n0", "val", 100); ·¢³öµÄÊý¾Ý¾ÍÊÇ n0.val=100
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void tjc_send_string(char* str)
{
    //µ±Ç°×Ö·û´®µØÖ·²»ÔÚ½áÎ² ²¢ÇÒ ×Ö·û´®Ê×µØÖ·²»Îª¿Õ
    while(*str!=0&&str!=0)
    {
        //·¢ËÍ×Ö·û´®Ê×µØÖ·ÖÐµÄ×Ö·û£¬²¢ÇÒÔÚ·¢ËÍÍê³ÉÖ®ºóÊ×µØÖ·×ÔÔö
        uart_send_char(*str++);
    }
	uart_send_char(0xff);
	uart_send_char(0xff);
	uart_send_char(0xff);
	return;
}

/********************************************************
º¯ÊýÃû£º  		tjc_send_txt
ÈÕÆÚ£º    	2024.09.18
¹¦ÄÜ£º    	´®¿Ú·¢ËÍ×Ö·û´®ºÍ½áÊø·û
ÊäÈë²ÎÊý£º		Òª·¢ËÍµÄ×Ö·û´®
·µ»ØÖµ£º 		ÎÞ
Ê¾Àý:			tjc_send_txt("t0", "txt", "ABC"); ·¢³öµÄÊý¾Ý¾ÍÊÇt0.txt="ABC"
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void tjc_send_txt(char* objname, char* attribute, char* txt)
{

    uart_send_string(objname);
    uart_send_char('.');
    uart_send_string(attribute);
    uart_send_string("=\"");
    uart_send_string(txt);
    uart_send_char('\"');
	uart_send_char(0xff);
	uart_send_char(0xff);
	uart_send_char(0xff);
	return;
}


/********************************************************
º¯ÊýÃû£º  		tjc_send_val
ÈÕÆÚ£º    	2024.09.18
¹¦ÄÜ£º    	´®¿Ú·¢ËÍ×Ö·û´®ºÍ½áÊø·û
ÊäÈë²ÎÊý£º		Òª·¢ËÍµÄ×Ö·û´®
·µ»ØÖµ£º 		ÎÞ
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void tjc_send_val(char* objname, char* attribute, int val)
{
	//Æ´½Ó×Ö·û´®,±ÈÈçn0.val=123
    uart_send_string(objname);
    uart_send_char('.');
    uart_send_string(attribute);
    uart_send_char('=');
    //CÓïÑÔÖÐÕûÐÎµÄÈ¡Öµ·¶Î§ÊÇ£º¡°-2147483648 ~ 2147483647¡±, ×î³¤Îª-2147483648,¼ÓÉÏ½áÊø·û\0Ò»¹²12¸ö×Ö·û
    char txt[12]="";
    intToStr(val, txt);
    uart_send_string(txt);
	uart_send_char(0xff);
	uart_send_char(0xff);
	uart_send_char(0xff);
	return;
}

/********************************************************
º¯ÊýÃû£º  		tjc_send_nstring
ÈÕÆÚ£º    	2024.09.18
¹¦ÄÜ£º    	´®¿Ú·¢ËÍ×Ö·û´®ºÍ½áÊø·û
ÊäÈë²ÎÊý£º		Òª·¢ËÍµÄ×Ö·û´®,×Ö·û´®³¤¶È
·µ»ØÖµ£º 		ÎÞ
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void tjc_send_nstring(char* str, unsigned char str_length)
{
    //µ±Ç°×Ö·û´®µØÖ·²»ÔÚ½áÎ² ²¢ÇÒ ×Ö·û´®Ê×µØÖ·²»Îª¿Õ
    for (int var = 0; var < str_length; ++var)
    {
        //·¢ËÍ×Ö·û´®Ê×µØÖ·ÖÐµÄ×Ö·û£¬²¢ÇÒÔÚ·¢ËÍÍê³ÉÖ®ºóÊ×µØÖ·×ÔÔö
        uart_send_char(*str++);
    }
	uart_send_char(0xff);
	uart_send_char(0xff);
	uart_send_char(0xff);
	return;
}

/********************************************************
º¯ÊýÃû£º  		initRingBuffer
ÈÕÆÚ£º    	2022.10.08
¹¦ÄÜ£º    	³õÊ¼»¯»·ÐÎ»º³åÇø
ÊäÈë²ÎÊý£º
·µ»ØÖµ£º 		void
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void initRingBuffer(void)
{
	//³õÊ¼»¯Ïà¹ØÐÅÏ¢
	ringBuffer.Head = 0;
	ringBuffer.Tail = 0;
	ringBuffer.Length = 0;
	return;
}

/********************************************************
º¯ÊýÃû£º  		write1ByteToRingBuffer
ÈÕÆÚ£º    	2022.10.08
¹¦ÄÜ£º    	Íù»·ÐÎ»º³åÇøÐ´ÈëÊý¾Ý
ÊäÈë²ÎÊý£º		ÒªÐ´ÈëµÄ1×Ö½ÚÊý¾Ý
·µ»ØÖµ£º 		void
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void write1ByteToRingBuffer(uint8_t data)
{
	if(ringBuffer.Length >= RINGBUFFER_LEN) //ÅÐ¶Ï»º³åÇøÊÇ·ñÒÑÂú
	{
	return ;
	}
	ringBuffer.Ring_data[ringBuffer.Tail]=data;
	ringBuffer.Tail = (ringBuffer.Tail+1)%RINGBUFFER_LEN;//·ÀÖ¹Ô½½ç·Ç·¨·ÃÎÊ
	ringBuffer.Length++;
	return ;
}

/********************************************************
º¯ÊýÃû£º  		deleteRingBuffer
×÷Õß£º
ÈÕÆÚ£º    	2022.10.08
¹¦ÄÜ£º    	É¾³ý´®¿Ú»º³åÇøÖÐÏàÓ¦³¤¶ÈµÄÊý¾Ý
ÊäÈë²ÎÊý£º		ÒªÉ¾³ýµÄ³¤¶È
·µ»ØÖµ£º 		void
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
void deleteRingBuffer(uint16_t size)
{
    if(size >= ringBuffer.Length)
    {
        initRingBuffer();
        return;
    }
    for(int i = 0; i < size; i++)
    {
        ringBuffer.Head = (ringBuffer.Head+1)%RINGBUFFER_LEN;
        ringBuffer.Length--;
    }
}

/********************************************************
º¯ÊýÃû£º  		read1ByteFromRingBuffer
×÷Õß£º
ÈÕÆÚ£º    	2022.10.08
¹¦ÄÜ£º    	´Ó´®¿Ú»º³åÇø¶ÁÈ¡1×Ö½ÚÊý¾Ý
ÊäÈë²ÎÊý£º		position:¶ÁÈ¡µÄÎ»ÖÃ
·µ»ØÖµ£º 		ËùÔÚÎ»ÖÃµÄÊý¾Ý(1×Ö½Ú)
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
uint8_t read1ByteFromRingBuffer(uint16_t position)
{
	uint16_t realPosition = (ringBuffer.Head + position) % RINGBUFFER_LEN;

	return ringBuffer.Ring_data[realPosition];
}

/********************************************************
º¯ÊýÃû£º  		getRingBufferLength
×÷Õß£º
ÈÕÆÚ£º    	2022.10.08
¹¦ÄÜ£º    	»ñÈ¡´®¿Ú»º³åÇøµÄÊý¾ÝÊýÁ¿
ÊäÈë²ÎÊý£º
·µ»ØÖµ£º 		´®¿Ú»º³åÇøµÄÊý¾ÝÊýÁ¿
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
uint16_t getRingBufferLength(void)
{
	return ringBuffer.Length;
}

/********************************************************
º¯ÊýÃû£º  		isRingBufferOverflow
×÷Õß£º
ÈÕÆÚ£º    	2022.10.08
¹¦ÄÜ£º    	ÅÐ¶Ï»·ÐÎ»º³åÇøÊÇ·ñÒÑÂú
ÊäÈë²ÎÊý£º
·µ»ØÖµ£º 		0:»·ÐÎ»º³åÇøÒÑÂú , 1:»·ÐÎ»º³åÇøÎ´Âú
ÐÞ¸Ä¼ÇÂ¼£º
**********************************************************/
uint8_t isRingBufferOverflow(void)
{
	return ringBuffer.Length < RINGBUFFER_LEN;
}


















