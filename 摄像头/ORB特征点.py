from maix import image, camera, display, app
import cv2
import time
import numpy as np

# ===== 可调参数配置区域 =====
# 1. 摄像头设置
CAM_WIDTH = 320      # 摄像头宽度
CAM_HEIGHT = 240     # 摄像头高度
CAM_FORMAT = image.Format.FMT_GRAYSCALE  # 直接获取灰度图像

# 2. 图像预处理参数
BLUR_KERNEL_SIZE = 5     # 高斯模糊核大小 (奇数)

# 3. ORB特征点参数
ORB_MAX_FEATURES = 500    # 保留的最大特征点数量
ORB_SCALE_FACTOR = 1.2    # 金字塔缩放因子
ORB_N_LEVELS = 8          # 金字塔层数
ORB_EDGE_THRESHOLD = 31   # 边缘阈值
ORB_FIRST_LEVEL = 0       # 第一层金字塔
ORB_WTA_K = 2             # 产生每个BRIEF描述子使用的像素点数
ORB_PATCH_SIZE = 31       # 用于方向计算的补丁大小
ORB_FAST_THRESHOLD = 20   # FAST检测阈值

# 4. 显示设置
SHOW_FPS = True          # 是否显示FPS
SHOW_KEYPOINTS = True    # 是否显示特征点
SHOW_DESCRIPTORS = False # 是否显示描述子(会降低性能)
FPS_UPDATE_INTERVAL = 1.0 # FPS显示间隔(秒)

# 5. 绘制样式
KEYPOINT_COLOR = (0, 0, 255)  # 特征点颜色 (B,G,R)
KEYPOINT_RADIUS = 3           # 特征点半径
KEYPOINT_THICKNESS = 1        # 特征点粗细

# ===== 主程序开始 =====
def main():
    # 初始化摄像头和显示
    cam = camera.Camera(CAM_WIDTH, CAM_HEIGHT, CAM_FORMAT)
    disp = display.Display()
    
    # 创建ORB检测器
    orb = cv2.ORB_create(
        nfeatures=ORB_MAX_FEATURES,
        scaleFactor=ORB_SCALE_FACTOR,
        nlevels=ORB_N_LEVELS,
        edgeThreshold=ORB_EDGE_THRESHOLD,
        firstLevel=ORB_FIRST_LEVEL,
        WTA_K=ORB_WTA_K,
        patchSize=ORB_PATCH_SIZE,
        fastThreshold=ORB_FAST_THRESHOLD
    )
    
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
        
        # 检测ORB特征点和计算描述子
        keypoints, descriptors = orb.detectAndCompute(blurred, None)
        
        # 创建彩色图像用于绘制
        output = cv2.cvtColor(gray_cv, cv2.COLOR_GRAY2BGR)
        
        # 绘制特征点
        if SHOW_KEYPOINTS:
            cv2.drawKeypoints(
                output, 
                keypoints, 
                output, 
                color=KEYPOINT_COLOR,
                flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS if SHOW_DESCRIPTORS else 0
            )
        
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
                print(f"FPS: {avg_fps:.1f} | 特征点: {len(keypoints)}")
                if SHOW_DESCRIPTORS and len(keypoints) > 0:
                    print(f"描述子维度: {descriptors.shape[1]}")
                frame_count = 0
                total_fps = 0
                last_display_time = time.time()

if __name__ == "__main__":
    main()