from maix import image, camera, display, app
import cv2
import time

# 实例化摄像头和显示对象
cam = camera.Camera(320, 240)
disp = display.Display()

# 八邻域方向定义（顺时针顺序）
directions = [
    (1, 0),   # 右
    (1, -1),  # 右上
    (0, -1),  # 上
    (-1, -1), # 左上
    (-1, 0),  # 左
    (-1, 1),  # 左下
    (0, 1),   # 下
    (1, 1)    # 右下
]

def eight_neighbor_tracing(binary_img, start_point):
    boundary = []
    current = start_point
    dir_idx = 0  # 起始搜索方向
    
    height, width = binary_img.shape[:2]
    
    while True:
        boundary.append(current)
        found = False
        
        # 从当前方向开始，顺时针搜索下一个边界点
        for i in range(8):
            search_dir = (dir_idx + 6 + i) % 8  # 从反方向开始搜索
            dx, dy = directions[search_dir]
            next_point = (current[0] + dx, current[1] + dy)
            
            # 检查是否在图像范围内
            if 0 <= next_point[0] < width and 0 <= next_point[1] < height:
                # 检查是否为前景点(白色255)
                if binary_img[next_point[1], next_point[0]] == 255:
                    dir_idx = search_dir
                    found = True
                    current = next_point
                    break
        
        # 终止条件：回到起点或找不到下一个点
        if not found or (len(boundary) > 2 and current == boundary[0]):
            break
            
        # 防止无限循环
        if len(boundary) > width * height:
            break
    
    return boundary

while not app.need_exit():
    start_time = time.time()
    
    # 读取摄像头图像
    img = cam.read()
    img_raw = image.image2cv(img, copy=False)
    
    # 图像预处理
    gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    
    # 寻找所有轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # 计算轮廓面积，过滤小噪点
        if cv2.contourArea(contour) < 100:
            continue
        
        # 找到轮廓的起始点（取第一个点）
        start_point = tuple(contour[0][0])
        
        # 使用八邻域算法追踪边界
        boundary = eight_neighbor_tracing(binary, start_point)
        
        # 绘制边界点
        for i in range(len(boundary)):
            if i > 0:
                cv2.line(img_raw, boundary[i-1], boundary[i], (0, 255, 0), 1)
            cv2.circle(img_raw, boundary[i], 2, (255, 0, 0), -1)
        
        # 绘制起始点（用不同颜色标记）
        if len(boundary) > 0:
            cv2.circle(img_raw, boundary[0], 5, (0, 0, 255), -1)
    
    # 显示处理后的图像
    img_show = image.cv2image(img_raw, copy=False)
    disp.show(img_show)
    
    # 计算并显示帧率
    fps = 1 / (time.time() - start_time)
    print("FPS: {:.1f}".format(fps))