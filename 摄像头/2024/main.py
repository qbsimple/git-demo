from maix import display, app, camera, ext_dev, image, nn, key, touchscreen, time
import cv2
import numpy as np

class WorkMode:
    Calibrate = 0 # 校准模式
    Running   = 1 # 正常运行模式

class DispMode:
    RGB = 0  # 显示RGB图像
    TOF = 1  # 显示TOF模块图像

# 全局上下文，可以理解成程序运行过程中的全局变量
_context = {
    'work_mode': WorkMode.Calibrate,
    'disp_mode': DispMode.RGB,
    'cali_step': 0,         # 当前校准步骤
    'last_pressed_time': -1, # 上次User按键按下的时刻

    'target_label': 'cup' # 要检测的目标
}

class CoordinateMapper:
    '''
    坐标映射器
    可将RGB图像中的矩形映射到TOF图像中的矩形
    '''
    def __init__(self, coordinates):
        '''
        参数为校准后所得到的坐标序列
        '''
        # Convert corners to numpy array
        dst_points = np.array([coordinates[4:]], dtype=np.float32)
        
        # Define source points for the perspective transform
        src_points = np.array([coordinates[0:4]], dtype=np.float32)
        # Compute the perspective transform matrix
        self._trans_matrix = cv2.getPerspectiveTransform(src_points, dst_points)

    def map_rect(self, x, y, width, height):
        '''
        传入RGB图像中的矩形参数，返回TOF图像中的矩形参数
        '''
        src_points = np.array([[[x, y], [x+width, y+height]]], dtype=np.float32)
        dst_points = cv2.perspectiveTransform(src_points, self._trans_matrix)[0]
        return (int(dst_points[0][0]), int(dst_points[0][1]), int(dst_points[1][0]-dst_points[0][0]), int(dst_points[1][1]- dst_points[0][1]))

def key_clicked(key_id, state):
    '''
    按键回调函数，User键按下的时候会自动调用
    '''
    global _context
    
    if state == key.State.KEY_PRESSED: # 按键按下 
        return
    elif state == key.State.KEY_LONG_PRESSED and key_id == key.Keys.KEY_OK: # OK键长按
        app.set_exit_flag(True)
        return

    _context['last_pressed_time'] = -1

    if key_id == key.Keys.KEY_OK: # MaixCam Pro设备左侧按键 User按键
        _context['disp_mode'] = DispMode.RGB if _context['disp_mode'] == DispMode.TOF else DispMode.TOF
    elif key_id == key.Keys.KEY_POWER: # MaixCam Pro设备左侧按键
        _context['work_mode'] = WorkMode.Calibrate if _context['work_mode'] == WorkMode.Running else WorkMode.Running
        

def main():
    global _context

    # 实例化YOLO检测器和TOF模块对象
    detector = nn.YOLO11(model="/root/models/yolo11n.mud", dual_buff=True)
    tof = ext_dev.tof100.Tof100(4, ext_dev.tof100.Resolution.RES_50x50, ext_dev.cmap.Cmap.JET, 40, 1000)

    # 实例化摄像头/显示/触摸屏/按键对象
    cam  = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
    disp = display.Display()
    touch = touchscreen.TouchScreen()
    _key  = key.Key(key_clicked)

    # 程序中间变量定义
    coordinate_mapper = None
    img_tof = None
    obj_tof_x = obj_tof_y = obj_tof_width = obj_tof_height = -1
    last_pressed = 0
    cali_step = 0

    # 保存校准过程中校准点坐标，前四个对应RGB图像中四个点，后四个对应TOF图像中四个点
    cali_coordinates = [[0, 0] for _ in range(8)]

    # 目标距离
    obj_distance = 40
    while not app.need_exit():
        # 读取RGB图像
        img_rgb = cam.read()

        # 目标检测并画出目标的外接矩形
        objs = detector.detect(img_rgb, conf_th = 0.5, iou_th = 0.45)
        if len(objs) > 0:
            for obj in objs:
                if detector.labels[obj.class_id] != _context['target_label']:
                    continue
                img_rgb.draw_rect(obj.x, obj.y, obj.w, obj.h, color = image.COLOR_RED, thickness = 2)        
        
                # 将RGB图像中目标外接矩形转换到TOF图像中
                if coordinate_mapper is not None:
                    obj_tof_x, obj_tof_y, obj_tof_width, obj_tof_height = coordinate_mapper.map_rect(obj.x, obj.y, obj.w, obj.h,)

        # 读取TOF图像
        if _context['disp_mode'] == DispMode.TOF:
            img_tof = tof.image()
            if img_tof is not None:
                img_tof.draw_rect(obj_tof_x, obj_tof_y, obj_tof_width, obj_tof_height, image.COLOR_WHITE)
        
        # 运行状态下，RGB图像显示模式下，获取TOF所测的目标框区域的距离
        if _context['work_mode'] == WorkMode.Running and _context['disp_mode'] == DispMode.RGB:

            # 获取距离矩阵
            distance_matrix = tof.matrix()
            distances = np.array(distance_matrix)
            # 切片出目标对象区域距离矩阵
            sub_distances = distances[obj_tof_y:obj_tof_y+obj_tof_height, obj_tof_x:obj_tof_x+obj_tof_width]

            #print(sub_distances)
            # 用目标区域中最小值作为最终目标距离
            if sub_distances.ndim == 2 and sub_distances.shape[0] > 0 and sub_distances.shape[1] > 0:
                distance_min = np.min(sub_distances)
                if distance_min > 40: # 异常值过滤，不能太小
                    obj_distance = distance_min 
            
            #print(obj_distance)

        # 校准模式下获取坐标
        if _context['work_mode'] == WorkMode.Calibrate:
            x, y, pressed = touch.read()
            if pressed != last_pressed:
                last_pressed = pressed

                # 触摸抬起的时候才进行逻辑操作
                if pressed == 0:
                    img_width = img_height = 0 
                    if _context['disp_mode'] == DispMode.RGB:
                        img_width, img_height = img_rgb.width(), img_rgb.height()
                    elif img_tof is not None:
                        img_width, img_height = img_tof.width(), img_tof.height()
                    
                    # 将屏幕触摸的坐标转换为图像的像素坐标
                    x, y = image.resize_map_pos_reverse(img_width, img_height, disp.width(), disp.height(), image.Fit.FIT_CONTAIN, x, y)
                    if (cali_coordinates[_context['cali_step']][0] != x or cali_coordinates[_context['cali_step']][1] != y):
                        cali_step = _context['cali_step']
                        cali_coordinates[cali_step] = [x, y]

                        # 操作完最后一个校准点后，初始化/实例化坐标映射器
                        if cali_step >= 7:
                            coordinate_mapper = CoordinateMapper(cali_coordinates)

                        # 更新校准步骤及显示模式
                        _context['cali_step'] = _context['cali_step'] + 1 if _context['cali_step'] < 7 else 0
                        _context['disp_mode'] = DispMode.RGB if _context['cali_step'] < 4 else DispMode.TOF

                        print(cali_coordinates)
            
            # 画出刚刚选出的校准点
            if cali_coordinates[cali_step] != (0, 0):
                if _context['disp_mode'] == DispMode.RGB:
                    img_rgb.draw_cross(cali_coordinates[cali_step][0], cali_coordinates[cali_step][1], image.COLOR_WHITE, 10, 2)
                elif img_tof is not None:
                    img_tof.draw_cross(cali_coordinates[cali_step][0], cali_coordinates[cali_step][1], image.COLOR_WHITE, 3, 1)

        # 显示图像            
        if _context['disp_mode'] == DispMode.RGB:
            if _context['work_mode'] == WorkMode.Calibrate: # 校准模式下，左上角显示 X 以表明当前处于校准模式
                img_rgb.draw_string(0, 0, 'X', image.COLOR_BLACK, 2, thickness= 2)
            else:
                img_rgb.draw_string(10, 10, 'Distance(mm): {}'.format(obj_distance), image.COLOR_YELLOW)
            disp.show(img_rgb)
        elif img_tof is not None:
            if _context['work_mode'] == WorkMode.Calibrate: # 校准模式下，左上角显示 X 以表明当前处于校准模式
                img_tof.draw_string(0, 0, 'X', image.COLOR_BLACK)
            disp.show(img_tof)

        # fps = time.fps()
        # print(f"time: {1000/fps:.02f}ms, fps: {fps:.02f}")

if __name__ == '__main__':
    main()