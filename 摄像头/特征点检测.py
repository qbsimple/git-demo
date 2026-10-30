from maix import image, camera, display, app
import cv2
import time
import numpy as np

# ===== 可调参数配置区域 =====
# 1. 摄像头设置
CAM_WIDTH = 320      # 摄像头宽度
CAM_HEIGHT = 240     # 摄像头高度
CAM_FORMAT = image.Format.FMT_GRAYSCALE  # 直接获取灰度图像

# 2. Canny边缘检测参数
BLUR_KERNEL_SIZE = 5     # 高斯模糊核大小 (奇数)
CANNY_THRESHOLD1 = 50    # Canny低阈值
CANNY_THRESHOLD2 = 150   # Canny高阈值
MIN_CONTOUR_AREA = 10    # 最小轮廓面积

# 3. 特征点检测参数 (FAST算法)
FAST_THRESHOLD = 20      # 特征点检测阈值
FAST_NONMAX_SUPPRESSION = True  # 是否使用非极大值抑制

# 4. 显示设置
SHOW_FPS = True          # 是否显示FPS
SHOW_FEATURES = True     # 是否显示特征点
FPS_UPDATE_INTERVAL = 1.0 # FPS显示间隔(秒)

# 5. 绘制样式
CONTOUR_COLOR = (0, 255, 0)  # 轮廓颜色 (B,G,R)
CONTOUR_THICKNESS = 1        # 轮廓粗细
FEATURE_COLOR = (255, 0, 0)  # 特征点颜色 (B,G,R)
FEATURE_RADIUS = 2           # 特征点半径
FEATURE_THICKNESS = -1       # 特征点粗细(-1表示填充)

# ===== 主程序开始 =====
def main():
    # 初始化摄像头和显示
    cam = camera.Camera(CAM_WIDTH, CAM_HEIGHT, CAM_FORMAT)
    disp = display.Display()
    
    # 创建FAST检测器
    fast = cv2.FastFeatureDetector_create(threshold=FAST_THRESHOLD, 
                                        nonmaxSuppression=FAST_NONMAX_SUPPRESSION)
    
    # 性能统计变量
    frame_count = 0
    total_fps = 0
    last_display_time = time.time()
    
    while not app.need_exit():
        start_time = time.time()
        
        # 捕获帧 - 直接获取灰度图
        gray_img = cam.read()
        gray_cv = image.image2cv(gray_img, copy=False)
        
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray_cv, (BLUR_KERNEL_SIZE, BLUR_KERNEL_SIZE), 0)
        
        # Canny边缘检测
        edges = cv2.Canny(blurred, CANNY_THRESHOLD1, CANNY_THRESHOLD2)
        
        # 轮廓检测
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 特征点检测
        keypoints = fast.detect(blurred, None)
        
        # 创建彩色图像用于绘制
        output = cv2.cvtColor(gray_cv, cv2.COLOR_GRAY2BGR)
        
        # 绘制轮廓
        for contour in contours:
            if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                continue
            cv2.drawContours(output, [contour], -1, CONTOUR_COLOR, CONTOUR_THICKNESS)
            
            if len(contour) > 0:
                start_point = tuple(contour[0][0])
  
        
        # 绘制特征点
        if SHOW_FEATURES:
            for kp in keypoints:
                x, y = int(kp.pt[0]), int(kp.pt[1])
                cv2.circle(output, (x, y), FEATURE_RADIUS, FEATURE_COLOR, FEATURE_THICKNESS)
        
        # 显示图像
        img_show = image.cv2image(output, copy=False)
        disp.show(img_show)
        
        # FPS显示
        if SHOW_FPS:
            frame_count += 1
            fps = 1 / (time.time() - start_time)
            total_fps += fps
            
            if time.time() - last_display_time > FPS_UPDATE_INTERVAL:
                avg_fps = total_fps / frame_count
                print(f"FPS: {avg_fps:.1f} | 特征点: {len(keypoints)} | 轮廓: {len(contours)}")
                frame_count = 0
                total_fps = 0
                last_display_time = time.time()

if __name__ == "__main__":
    main()