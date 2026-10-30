#include "ml_hmc5883l.h"

int16_t hmc_x, hmc_y, hmc_z;
float yaw_hmc;

void HMC5883L_Write(uint8_t addr, uint8_t dat)
{
	MPU_IIC_Start();
	MPU_IIC_Send_Byte(HMC5883L_ADDR);
	MPU_IIC_Wait_Ack();
	MPU_IIC_Send_Byte(addr);
	MPU_IIC_Wait_Ack();
	MPU_IIC_Send_Byte(dat);
	MPU_IIC_Wait_Ack();
	MPU_IIC_Stop();
}

uint8_t HMC5883L_Read(uint8_t addr)
{
	MPU_IIC_Start();
	MPU_IIC_Send_Byte(HMC5883L_ADDR);
	MPU_IIC_Wait_Ack();
	MPU_IIC_Send_Byte(addr);
	MPU_IIC_Wait_Ack();
	MPU_IIC_Stop();
	
	MPU_IIC_Start();
	MPU_IIC_Send_Byte(HMC5883L_ADDR | 0x01);
	MPU_IIC_Wait_Ack();
	uint8_t dat = MPU_IIC_Read_Byte(0);
//	I2C_NotSendAck();
	MPU_IIC_Stop();
	
	return dat;
}

void HMC5883L_Init()
{
	HMC5883L_Write(HMC5883L_CRA, 0xf8);  // 最大输出速率（75HZ）
	HMC5883L_Write(HMC5883L_CRB, 0x20);  // 默认增益
	HMC5883L_Write(HMC5883L_MR, 0x00);   // 连续测量
}

void HMC5883L_GetData()
{
	uint8_t data_h, data_l;
	data_h = HMC5883L_Read(HMC5883L_DOXMR);
	data_l = HMC5883L_Read(HMC5883L_DOXLR);
	hmc_x = data_l | (data_h << 8);

	data_h = HMC5883L_Read(HMC5883L_DOYMR);
	data_l = HMC5883L_Read(HMC5883L_DOYLR);
	hmc_y = data_l | (data_h << 8);

	data_h = HMC5883L_Read(HMC5883L_DOZMR);
	data_l = HMC5883L_Read(HMC5883L_DOZLR);
	hmc_z = data_l | (data_h << 8);
}




	


