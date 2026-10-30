# # 导入所需的库和模块
# from maix import camera, display, image, nn, app, uart, time
# import struct
# import sys

# # 添加自定义模块路径
# sys.path.append('/root/exam')
# import serial_protocol

# # 初始化 RetinaFace 人脸检测模型，加载预训练模型
# detector = nn.Retinaface(model="/root/models/retinaface.mud")

# # 初始化摄像头，设置摄像头的分辨率与模型输入一致
# cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())

# # 初始化显示对象
# dis = display.Display()

# # 初始化串口通信协议
# comm_proto = serial_protocol.SerialProtocol()

# # 设置串口设备路径和波特率
# device = "/dev/ttyS0"
# serial = uart.UART(device, 115200)

# try:
#     # 主循环，直到应用程序需要退出
#     while not app.need_exit():
#         # 从摄像头读取一帧图像
#         img = cam.read()
#         if img is None:
#             continue  # 如果未读取到图像，跳过本次循环

#         # 使用 RetinaFace 模型检测图像中的人脸
#         # conf_th 是置信度阈值，iou_th 是交并比阈值
#         objs = detector.detect(img, conf_th=0.4, iou_th=0.45)

#         # 遍历检测到的每个人脸
#         for obj in objs:
#             # 在图像上绘制红色矩形框，框出人脸
#             img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)

#             # 将人脸框的坐标打包为二进制数据
#             # '<iiii' 表示小端序的 4 个整数
#             payload = struct.pack('<iiii', obj.x, obj.y, obj.w, obj.h)

#             # 使用通信协议编码数据
#             encoded = comm_proto.encode(payload)

#             # 将编码后的数据通过串口发送
#             serial.write(encoded)

#             # 打印编码后的数据（十六进制格式）
#             print(encoded.hex(' '))

#         # 在屏幕上显示处理后的图像
#         dis.show(img)

#         # 添加延时，避免循环过快占用过多 CPU 资源
#         time.sleep_ms(50)

# except Exception as e:
#     # 捕获异常并打印错误信息
#     print(f"程序运行出错: {e}")

# finally:
#     # 程序退出时释放资源
#     cam.close()
#     serial.close()
#     print("程序退出，资源已释放")


# 导入所需的库和模块
from maix import camera, display, image, app, uart, time
import struct
import sys

# 添加自定义模块路径
sys.path.append('/root/exam')
import serial_protocol

# 初始化摄像头，设置摄像头的分辨率
_image_width = 320
_image_height = 240
cam = camera.Camera(_image_width, _image_height)

# 初始化显示对象
dis = display.Display()

# 初始化串口通信协议
comm_proto = serial_protocol.SerialProtocol()

# 设置串口设备路径和波特率
device = "/dev/ttyS0"
serial = uart.UART(device, 115200)

def send_line_data(angle, offset):
    '''
    将线条的角度和偏移量打包并通过串口发送
    '''
    # 打包数据：角度（float）和偏移量（int）
    payload = struct.pack('<fi', angle, offset)
    encoded = comm_proto.encode(payload)
    serial.write(encoded)
    print(f"Sent data: angle={angle}, offset={offset}")

try:
    # 主循环，直到应用程序需要退出
    while not app.need_exit():
        # 从摄像头读取一帧图像
        img = cam.read()
        if img is None:
            continue  # 如果未读取到图像，跳过本次循环

        # 假设我们检测到一条线，计算其角度和偏移量
        # 这里我们使用简单的示例值，实际应用中需要根据图像处理结果计算
        angle = 45.0  # 线条角度
        offset = 10   # 线条中心相对于图像中心的偏移量

        # 发送线条数据给单片机
        send_line_data(angle, offset)

        # 在屏幕上显示处理后的图像
        dis.show(img)

        # 添加延时，避免循环过快占用过多 CPU 资源
        time.sleep_ms(50)

except Exception as e:
    # 捕获异常并打印错误信息
    print(f"程序运行出错: {e}")

finally:
    # 程序退出时释放资源
    cam.close()
    serial.close()
    print("程序退出，资源已释放")
