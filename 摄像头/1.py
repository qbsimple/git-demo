# from maix import image, display

# disp = display.Display()
# img = image.Image(320, 240)
# img.draw_rect(0, 0, disp.width(), disp.height(), color=image.Color.from_rgb(255, 0, 0), thickness=-1)
# img.draw_rect(10, 10, 100, 30, color=image.Color.from_rgb(0, 255, 0))
# img.draw_string(10, 0, "Hello MaixPy!", color=image.Color.from_rgb(255, 255, 255))
# disp.show(img)


# from maix import camera, display, app,time,image

# disp = display.Display()
# cam = camera.Camera(640, 480,image.Format.FMT_RGB888)	
# # cam = camera.Camera(640, 480, image.Format.FMT_GRAYSCALE)	# 设置输出灰度图像
# # cam = camera.Camera(640, 480, image.Format.FMT_YVU420SP)	# 设置输出NV21图像
# cam.exp_mode(0)             #自动曝光模式
# # cam.awb_mode(0)			# 0,开启白平衡;1,关闭白平衡
# cam.luma(50)		    # 设置亮度，范围[0, 100]
# cam.constrast(50)		# 设置对比度，范围[0, 100]
# cam.saturation(50)		# 设置饱和度，范围[0, 100]
# disp.set_backlight(50)  #显示器的背光亮度
# cam.skip_frames(30)           # 跳过开头的30帧
# while not app.need_exit():
#     img = cam.read()
#     img.draw_rect(200, 200, 100, 100, image.Color.from_rgb(255, 255, 255,),thickness=1)
#     disp.show(img)

#     fps = time.fps()            # Calculate FPS between last time fps() call and this time call.
#                                 # | 计算两次 fps 函数调用之间的帧率
#     print(f"time: {1000/fps:.02f}ms, fps: {fps:.02f}") # print FPS in console
#                                                        # | 在终端打印帧率（FPS）


# from maix import camera, display, app,time,image
# disp = display.Display()
# img = image.Image(640, 480, image.Format.FMT_RGB888)
# img.draw_rect(200, 200, 100, 100, image.Color.from_rgb(255, 0, 0,),thickness=1)
# # img.draw_rect(10, 10, 100, 100, image.Color.from_rgb(255, 0, 0,),thickness=-1)
# img.draw_string(200, 120, " MaixPy", image.Color.from_rgb(255, 0, 0),scale=3)
# img.draw_line(200, 200, 300, 300, image.Color.from_rgb(255, 255, 0))
# img.draw_circle(200, 200,100, image.Color.from_rgb(255, 0, 0))
# keypoints = [10, 10, 100, 10, 10, 100,200,200]
# img.draw_keypoints(keypoints, image.Color.from_rgb(255, 0, 0), size=10, thickness=1)
# img.draw_cross(300, 300, image.Color.from_rgb(255, 0, 0), size=5, thickness=1)
# img.draw_arrow(10, 10, 300, 400, image.Color.from_rgb(255, 0, 0), thickness=1)



# disp.show(img)



# from maix import touchscreen, app, time

# # 初始化触摸屏对象
# ts = touchscreen.TouchScreen()

# # 初始化变量
# pressed_already = False  # 记录是否已经按下
# last_x = 0  # 上一次的 X 坐标
# last_y = 0  # 上一次的 Y 坐标
# last_pressed = False  # 上一次的按下状态

# # 主循环
# while not app.need_exit():
#     # 读取触摸屏状态
#     x, y, pressed = ts.read()

#     # 如果状态发生变化，打印当前状态
#     if x != last_x or y != last_y or pressed != last_pressed:
#         print(x, y, pressed)
#         last_x = x
#         last_y = y
#         last_pressed = pressed

#     # 检测点击事件
#     if pressed:
#         pressed_already = True  # 标记为已按下
#     else:
#         if pressed_already:
#             print(f"clicked, x: {x}, y: {y}")  # 打印点击事件
#             pressed_already = False  # 重置按下标记

#     # 休眠 1 毫秒以减少 CPU 占用
#     time.sleep_ms(1)


# from maix import image, camera, display

# cam = camera.Camera(640, 480)
# disp = display.Display()

# # 根据色块颜色选择对应配置每个颜色阈值的格式为 [L_MIN, L_MAX, A_MIN, A_MAX, B_MIN,
# # thresholds = [[0, 80, 40, 80, 10, 80]]      # red
# thresholds = [[0, 80, -120, -10, 0, 30]]    # green
# # thresholds = [[0, 60, 0, 127, -128, -35]]  # blue
# # thresholds = [[0, 50, 0, 50, 0, 50]]  # 黑色

# while 1:
#     img = cam.read()
#     blobs = img.find_blobs(thresholds, pixels_threshold=500)
#     for blob in blobs:
#         img.draw_rect(blob[0], blob[1], blob[2], blob[3], image.COLOR_GREEN)
#     disp.show(img)


# from maix import camera, display, image

# cam = camera.Camera(320, 240,image.Format.FMT_GRAYSCALE)
# disp = display.Display()

# # thresholds = [[0, 80, 40, 80, 10, 80]]      # red
# # thresholds = [[0, 80, -120, -10, 0, 30]]    # green
# # thresholds = [[0, 80, 30, 100, -120, -60]]  # blue
# # thresholds = [[80, 100, -20, 20, -20, 20]]  # 白色阈值
# # thresholds = [[0, 50, 0, 50, 0, 50]]  # 灰色
# # thresholds = [[0, 50, -79, 127, -73, 74]]  # 灰色
# while 1:
#     img = cam.read()

#     lines = img.get_regression(thresholds, area_threshold = 100)
#     for a in lines:
#         img.draw_line(a.x1(), a.y1(), a.x2(), a.y2(), image.COLOR_GREEN, 2)
#         theta = a.theta()
#         rho = a.rho()
#         if theta > 90:
#             theta = 270 - theta
#         else:
#             theta = 90 - theta
#         img.draw_string(0, 0, "theta: " + str(theta) + ", rho: " + str(rho), image.COLOR_BLUE)

#     disp.show(img)


# from maix import image, camera, display

# cam = camera.Camera(320, 240)
# disp = display.Display()

# while 1:
#     img = cam.read()
#     qrcodes = img.find_qrcodes()
#     for qr in qrcodes:
#         corners = qr.corners()
#         for i in range(4):
#             img.draw_line(corners[i][0], corners[i][1], corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], image.COLOR_RED)
#         img.draw_string(qr.x(), qr.y() - 15, qr.payload(), image.COLOR_RED)
#     disp.show(img)




# from maix import camera, display, app, image

# # 初始化摄像头，分辨率为 320x224
# cam = camera.Camera(320, 224)
# # 初始化显示屏
# disp = display.Display()
# # 初始化二维码检测器
# detector = image.QRCodeDetector()

# # 主循环，直到应用程序需要退出
# while not app.need_exit():
#     try:
#         # 从摄像头读取一帧图像
#         img = cam.read()

#         # 检测图像中的二维码
#         qrcodes = detector.detect(img)
        
#         # 遍历所有检测到的二维码
#         for q in qrcodes:
#             # 获取二维码的四个角点
#             corners = q.corners()
#             # 绘制二维码的边框
#             for i in range(4):
#                 img.draw_line(corners[i][0], corners[i][1],
#                               corners[(i + 1) % 4][0], corners[(i + 1) % 4][1],
#                               image.COLOR_RED)
#             # 在二维码上方显示二维码的内容（payload）
#             img.draw_string(q.x(), q.y() - 15, "payload: " + q.payload(), image.COLOR_BLUE)

#         # 在显示屏上显示处理后的图像
#         disp.show(img)
#     except Exception as e:
#         print("Error:", e)
#         continue


# from maix import pinmap
# f=pinmap.get_pin_functions("A19")
# print(f)




# from maix import gpio, pinmap, time

# pinmap.set_pin_function("B3", "GPIOB3")
# led = gpio.GPIO("GPIOB3", gpio.Mode.OUT)
# led.value(0)

# while 1:
#     led.toggle()
#     time.sleep_ms(500)

from maix import app, uart, pinmap, time
import struct

device = "/dev/ttyS0"
serial0 = uart.UART('/dev/ttyS0', 115200)

# data = "hello 1\r\n".encode()
# serial0.write(data)
# print("sent:", data)

# data = "hellojklkjjkj 2\r\n"
# serial0.write_str(data)
# print("sent:", data)


data = "object {} at x: {} y: {} w: {} h: {}, prob: {:.2f}\r\n".format("apple", 100, 100, 80, 80, 0.98123)
serial0.write_str(data)
print("sent:", data)


print("now wait receive data:")
while not app.need_exit():
    data = serial0.read()
    if data:
        print("Received, type: {}, len: {}, data: {}".format(type(data), len(data), data))

    time.sleep_ms(1000)  # 增加延时