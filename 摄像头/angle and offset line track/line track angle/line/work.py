# 导入所需的库和模块
from maix import camera, display, image, nn, app, uart, time
import struct
import sys

# 添加自定义模块路径
sys.path.append('/root/exam')
import serial_protocol

# 初始化摄像头，设置摄像头的分辨率与模型输入一致
# 假设模型输入为 640, 480，格式为 RGB
cam = camera.Camera(640, 480, image.Format.FMT_RGB888)

# 初始化显示对象
dis = display.Display()

# 初始化串口通信协议
comm_proto = serial_protocol.SerialProtocol()

# 设置串口设备路径和波特率
device = "/dev/ttyS0"
serial = uart.UART(device, 115200)

try:
    # 主循环，直到应用程序需要退出
    while not app.need_exit():
        # 从摄像头读取一帧图像
        img = cam.read()
        if img is None:
            continue  # 如果未读取到图像，跳过本次循环

        # 在这里添加自定义的图像处理或对象检测逻辑
        # 例如：检测图像中的对象并获取其坐标
        # objs = custom_detector.detect(img)

        # 假设 objs 是一个包含对象信息的列表，每个对象有 x, y, w, h 属性
        objs = []  # 替换为实际的对象检测结果

        # 遍历检测到的每个对象
        for obj in objs:
            # 在图像上绘制矩形框，框出对象
            img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)

            # 将对象框的坐标打包为二进制数据
            # '<iiii' 表示小端序的 4 个整数
            payload = struct.pack('<iiii', obj.x, obj.y, obj.w, obj.h)

            # 使用通信协议编码数据
            encoded = comm_proto.encode(payload)

            # 将编码后的数据通过串口发送
            serial.write(encoded)

            # 打印编码后的数据（十六进制格式）
            print(encoded.hex(' '))

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