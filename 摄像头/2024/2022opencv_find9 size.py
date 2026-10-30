from maix import image, camera, display, app
import cv2
import time
import numpy as np

# 颜色阈值
RED_LOWER1 = np.array([0, 100, 100])
RED_UPPER1 = np.array([10, 255, 255])
RED_LOWER2 = np.array([160, 100, 100])
RED_UPPER2 = np.array([180, 255, 255])
BLUE_LOWER = np.array([90, 100, 100])
BLUE_UPPER = np.array([130, 255, 255])

def shape_judge(contour):
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return None
    
    circularity = (4 * np.pi * area) / (perimeter ** 2)
    approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
    num_sides = len(approx)
    
    if num_sides == 3:
        return 1  # Triangle
    elif circularity > 0.8:
        return 2  # Circle
    elif num_sides == 4:
        return 3  # Rectangle
    return None

def main():
    try:
        cam = camera.Camera(320, 240, image.Format.FMT_RGB888)
    except:
        cam = camera.Camera()
    
    disp = display.Display()
    
    while not app.need_exit():
        try:
            img = cam.read()
            img_cv = image.image2cv(img)
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            output = img_cv.copy()

            # 红色检测
            red_mask = cv2.bitwise_or(
                cv2.inRange(hsv, RED_LOWER1, RED_UPPER1),
                cv2.inRange(hsv, RED_LOWER2, RED_UPPER2))
            
            # 蓝色检测
            blue_mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)

            # 处理检测结果
            for mask, color, name in [(red_mask, (0, 0, 255), "Red"), 
                                    (blue_mask, (255, 0, 0), "Blue")]:
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    cnt = max(contours, key=cv2.contourArea)
                    shape = shape_judge(cnt)
                    x, y, w, h = cv2.boundingRect(cnt)
                    
                    if shape == 1:
                        text = f"{name} Triangle"
                    elif shape == 2:
                        text = f"{name} Circle"
                    elif shape == 3:
                        text = f"{name} Rectangle"
                    else:
                        continue
                    
                    cv2.drawContours(output, [cnt], -1, color, 2)
                    cv2.putText(output, text, (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            disp.show(image.cv2image(output))
            
        except Exception as e:
            print(f"Error: {str(e)}")  # 保持错误信息为英文
            time.sleep(0.1)

if __name__ == "__main__":
    main()