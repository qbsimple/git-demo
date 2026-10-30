from maix import image, camera, display, app
import cv2
import time
import numpy as np

# ===== 可调参数配置区域 =====
# 1. 摄像头设置
CAM_WIDTH = 320      # 摄像头宽度 (可降低到160提升帧率)
CAM_HEIGHT = 240     # 摄像头高度 (可降低到120提升帧率)
CAM_FORMAT = image.Format.FMT_GRAYSCALE  # 直接获取灰度图像

# 2. Canny边缘检测参数
BLUR_KERNEL_SIZE = 5     # 高斯模糊核大小 (奇数)
CANNY_THRESHOLD1 = 50    # Canny低阈值
CANNY_THRESHOLD2 = 150   # Canny高阈值
MIN_CONTOUR_AREA = 10    # 最小轮廓面积 (过滤小噪点)

# 3. 显示设置
SHOW_FPS = True          # 是否显示FPS
FPS_UPDATE_INTERVAL = 1.0 # FPS显示间隔(秒)

# 4. 轮廓绘制样式
CONTOUR_COLOR = (0, 255, 0)  # 轮廓颜色 (B,G,R)
CONTOUR_THICKNESS = 1        # 轮廓粗细
START_POINT_COLOR = (0, 0, 255)  # 起点颜色 (B,G,R)
START_POINT_RADIUS = 3       # 起点半径

# ===== 主程序开始 =====
def main():
    # 初始化摄像头和显示 - 直接获取灰度图像
    cam = camera.Camera(CAM_WIDTH, CAM_HEIGHT, CAM_FORMAT)
    disp = display.Display()
    
    # 性能统计变量
    frame_count = 0
    total_fps = 0
    last_display_time = time.time()
    
    while not app.need_exit():
        start_time = time.time()
        
        # 捕获帧 - 直接获取灰度图
        gray_img = cam.read()
        gray_cv = image.image2cv(gray_img, copy=False)
        
        # 高斯模糊(小内核)
        blurred = cv2.GaussianBlur(gray_cv, (BLUR_KERNEL_SIZE, BLUR_KERNEL_SIZE), 0)
        
        # Canny边缘检测
        edges = cv2.Canny(blurred, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
        
        # 轮廓检测优化
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 创建彩色图像用于绘制(只在需要显示时转换)
        output = cv2.cvtColor(gray_cv, cv2.COLOR_GRAY2BGR) if len(contours) > 0 else None
        
        for contour in contours:
            if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                continue
            
            # 延迟创建输出图像(只有当有轮廓时才转换)
            if output is None:
                output = cv2.cvtColor(gray_cv, cv2.COLOR_GRAY2BGR)
            
            # 绘制轮廓和起点
            cv2.drawContours(output, [contour], -1, CONTOUR_COLOR, CONTOUR_THICKNESS)
            
            if len(contour) > 0:
                start_point = tuple(contour[0][0])
                cv2.circle(output, start_point, START_POINT_RADIUS, START_POINT_COLOR, -1)
        
        # 显示图像(如果没有轮廓则显示原始灰度图)
        img_show = image.cv2image(output if output is not None else gray_cv, copy=False)
        disp.show(img_show)
        
        # FPS显示
        if SHOW_FPS:
            frame_count += 1
            fps = 1 / (time.time() - start_time)
            total_fps += fps
            
            if time.time() - last_display_time > FPS_UPDATE_INTERVAL:
                avg_fps = total_fps / frame_count
                print(f"FPS: {avg_fps:.1f} | Resolution: {CAM_WIDTH}x{CAM_HEIGHT}")
                frame_count = 0
                total_fps = 0
                last_display_time = time.time()

if __name__ == "__main__":
    main()