#include "ml_i2c.h"

//#define SDA_Output(x)  gpio_set(I2C_GPIO, I2C_SDA_GPIO_Pin, x)
#define SDA_Set()  HAL_GPIO_WritePin(GPIOB,GPIO_PIN_8,GPIO_PIN_SET)//设置SCL高电平
#define SDA_Clr()  HAL_GPIO_WritePin(GPIOB,GPIO_PIN_8,GPIO_PIN_RESET)//设置SCL高电平
#define SCL_Set()   HAL_GPIO_WritePin(GPIOB,GPIO_PIN_9,GPIO_PIN_SET)
#define SCL_Clr()   HAL_GPIO_WritePin(GPIOB,GPIO_PIN_9,GPIO_PIN_RESET)




#define SDA_Input() HAL_GPIO_ReadPin(GPIOB,OLED_SDA_Pin)

void I2C_Init()
{
	SDA_Set() ;
	SCL_Set();
}

// 起始信号
void I2C_Start()
{
	SDA_Set() ;
	SCL_Set();
	SDA_Clr();
	SCL_Clr();
}

// 终止信号 
void I2C_Stop()
{
	SDA_Clr();
	SCL_Set();
	SDA_Set() ;
}

// 主机发送一个字节
void I2C_SendByte(uint8_t byte)
{
	for(int i = 0; i < 8; i++)
	{
		if(byte & (0x80>>i))
			SDA_Set() ;
		else
			SDA_Clr();
		SCL_Set();
		SCL_Clr();
	}
}

// 主机接收一个字节
uint8_t I2C_ReceiveByte()
{
	uint8_t byte = 0;
	SDA_Set() ;
	for(int i = 0; i < 8; i++)
	{
		SCL_Set();
		if(SDA_Input())
			byte |= (0x80>>i);
		SCL_Clr();
	}
	
	return byte;
}

// 主机应答 
void I2C_SendAck()
{
	SDA_Clr();
	SCL_Set();
	SCL_Clr();
}

// 主机不应答 
void I2C_NotSendAck()
{
	SDA_Set() ;
	SCL_Set();
	SCL_Clr();
}

// 等待从机应答 
uint8_t I2C_WaitAck()
{
	uint8_t byte = 0;
	SDA_Set() ;
	SCL_Set();
	byte = SDA_Input();
	SCL_Clr();
	
	return byte;
}

