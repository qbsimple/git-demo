# from maix import camera, display, image, nn, app, uart
# import struct

import sys
sys.path.append('/root/exam')
# import serial_protocol
# # 初始化Retinaface人脸检测器
# detector = nn.Retinaface(model="/root/models/retinaface.mud")

# # 初始化摄像头和显示
# cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
# dis = display.Display()

# # 初始化串口通信
# comm_proto = serial_protocol.SerialProtocol()
# device = "/dev/tty50"
# serial = uart.UART(device, 115200)

# data_buffer = bytearray()

# while not app.need_exit():
#     img = cam.read()
#     objs = detector.detect(img, conf_th=0.4, iou_th=0.45)
    
#     for obj in objs:
#         img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
#         print(obj.x, obj.y, obj.w, obj.h)
#         payload = struct.pack('<iiii', obj.x, obj.y, obj.w, obj.h)
        
#         encoded = comm_proto.encode(payload)
#         serial.write(encoded)
    
#     length = serial.available()
#     if length > 0:
#         data = serial.read(length)
#         data_buffer += data
#         rc, bytes_redundant = comm_proto.is_valid(data_buffer)
        
#         if bytes_redundant > 0:
#             data_buffer = data_buffer[bytes_redundant:]
        
#         if rc >= 0:
#             result = comm_proto.decode(data_buffer)
#             if len(result) == 16:
#                 x, y, w, h = struct.unpack('<iiii', result)
#                 print('{},{},{},{}'.format(x, y, w, h))
    
#     packet_length = comm_proto.length(data_buffer)
#     data_buffer = data_buffer[packet_length:]
    
#     dis.show(img)


from maix import camera, display, image, nn, app, uart, time
import struct
import serial_protocol

detector = nn.Retinaface(model="/root/models/retinaface.mud")

cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
dis = display.Display()

comm_proto = serial_protocol.SerialProtocol()
device = "/dev/ttyS0"
serial = uart.UART(device, 115200)

while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th = 0.4, iou_th = 0.45)
    for obj in objs:
        img.draw_rect(obj.x, obj.y, obj.w, obj.h, color = image.COLOR_RED)
        print(obj.x, obj.y, obj.w, obj.h)
        payload = struct.pack('<iiii',obj.x,obj.y,obj.w,obj.h)
        
        encoded = comm_proto.encode(payload)
        serial.write(encoded)
        # print(encoded.hex(' '))
    time.sleep_ms(50)

    dis.show(img)
