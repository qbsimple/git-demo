#include "head.h"
#include "motor.h"
extern TIM_HandleTypeDef htim9;
/**
  * @brief 绝对值函数
  * @param num: 输入整数
  * @return 返回 num 的绝对值
  * @note 使用条件运算符计算绝对值
  */
int myabs(int num) {
    return (num < 0) ? -num : num;
}

/**
  * @brief 使右电机正转
  * @note 设置BIN1为0，BIN2为1，使电机向前转动
  */
void Motor_Right() {
    HAL_GPIO_WritePin(BIN1_GPIO_Port, BIN1_Pin, GPIO_PIN_RESET); // BIN1 = 0
    HAL_GPIO_WritePin(BIN2_GPIO_Port, BIN2_Pin, GPIO_PIN_SET);   // BIN2 = 1
}

/**
  * @brief 使右电机反转
  * @note 设置BIN1为1，BIN2为0，使电机向后转动
  */
void Motor_Right1() {
    HAL_GPIO_WritePin(BIN1_GPIO_Port, BIN1_Pin, GPIO_PIN_SET);   // BIN1 = 1
    HAL_GPIO_WritePin(BIN2_GPIO_Port, BIN2_Pin, GPIO_PIN_RESET); // BIN2 = 0
}

/**
  * @brief 使左电机正转
  * @note 设置AIN1为1，AIN2为0，使电机向前转动
  */
void Motor_Left() {
    HAL_GPIO_WritePin(AIN1_GPIO_Port, AIN1_Pin, GPIO_PIN_SET); // AIN1 = 1
    HAL_GPIO_WritePin(AIN2_GPIO_Port, AIN2_Pin, GPIO_PIN_RESET);   // AIN2 = 0
}

/**
  * @brief 使左电机反转
  * @note 设置AIN1为0，AIN2为1，使电机向后转动
  */
void Motor_Left1() {
    HAL_GPIO_WritePin(AIN1_GPIO_Port, AIN1_Pin, GPIO_PIN_RESET);   // AIN1 = 0
    HAL_GPIO_WritePin(AIN2_GPIO_Port, AIN2_Pin, GPIO_PIN_SET); // AIN2 = 1
}

/**
  * @brief 设置电机速度
  * @param motor_right: 右电机的速度（正值表示正转，负值表示反转）
  * @param motor_left: 左电机的速度（正值表示正转，负值表示反转）
  * @note 使用PWM调节电机转速
  */
void Motor_Set(int motor_right, int motor_left) {
    int pwmb_abs; // 右电机PWM值
    int pwma_abs; // 左电机PWM值

    // 设置右电机转动方向
    if (motor_right > 0) {
        Motor_Right(); // 右电机正转
    } else {
        Motor_Right1(); // 右电机反转
    }

    // 设置左电机转动方向
    if (motor_left > 0) {
        Motor_Left(); // 左电机正转
    } else {
        Motor_Left1(); // 左电机反转
    }

    // 计算右电机的PWM值（绝对值）
    pwmb_abs = myabs(motor_right); // 右电机PWM值
    pwma_abs = myabs(motor_left);  // 左电机PWM值

    // 限制PWM值最大为99
    if (motor_right > 99) motor_right = 99;
    if (motor_left > 99) motor_left = 99;

    // 设置PWM输出
    __HAL_TIM_SET_COMPARE(&htim9, TIM_CHANNEL_1, pwmb_abs); // 设置右电机PWM
    __HAL_TIM_SET_COMPARE(&htim9, TIM_CHANNEL_2, pwma_abs); // 设置左电机PWM
}










