from maix import camera, display,image, touchscreen, app, time,nn
from maix import uart
import os,math


# ---------- 0. 参数 ----------
# ★ 1. 把 THRESH / STABLE_N 的默认值改成从文件读取
THRESH  = 4
STABLE_N = 2

# ★ 2. 读取文件（放在所有初始化最前，保证后面用到的是文件里的值）
THRESHOLD_FILE = "/mnt/data/my_thresholds.txt"
try:
    with open(THRESHOLD_FILE, "r") as f:
        for ln in f:
            ln = ln.strip()
            if ln.startswith("thresh:"):
                THRESH = int(ln.split(":")[1])
            elif ln.startswith("stable:"):
                STABLE_N = int(ln.split(":")[1])
except Exception:
    pass        # 文件不存在或格式错误就用上面默认值

# ---------- 1. 模型 ----------
detector = nn.YOLO11(model="/root/models/my_model3/yolo11n_int8.mud", dual_buff=True)
# labels  = ["1","2","3","4","5","6","7","8"]
labels  = ["kongque","lang","hou","hu"]
CLS_NUM = len(labels)
# 4 个类别对应的颜色
CLS_COLORS = [image.COLOR_RED,
              image.COLOR_BLUE,
              image.COLOR_GREEN,
              image.COLOR_YELLOW]
THRESH  = 4            # 稳定门限
DECAY   = 0.5           # 衰减系数
STABLE_N = 2            # 连续帧数确认


#摄像头配置
disp = display.Display()
cam = camera.Camera(320, 240,fps=60)   #QVGA,fps也可选80
# cam = camera.Camera(160, 120,fps=60)   #QQVGA,fps也可选80
disp.set_backlight(40)  #设置背光亮度(0-100)
# cam.awb_mode(0)		    # 0,开启白平衡;1,关闭白平衡
# cam.exp_mode(0)         #设置为自动曝光
# cam.gain(10)           #设置增益(注意设置增益后，摄像头会切换到手动曝光模式)
# cam.exposure(550)      #设置曝光时间(注意设置曝光时间后，摄像头会切换到手动曝光模式)
cam.luma(40)		    # 设置亮度，范围[0, 100]
cam.constrast(50)		# 设置对比度，范围[0, 100]
cam.saturation(50)		# 设置饱和度，范围[0, 100]
cam.skip_frames(30)     # 跳过开头的30帧，让相机图像在改变相机设置后稳定下来
#串口配置及相关参数
device = "/dev/ttyS0" #选择USB引出的串口
serial = uart.UART(device, 115200) #设置串口波特率
# 触摸屏配置 及 相关触摸参数
ts = touchscreen.TouchScreen() 
torch_flag = False
torch_success = False #松手抬起，该标志位置1
# 屏幕宽度和高度
_image_width = 320  # 定义图像宽度为320像素
_image_height = 240  # 定义图像高度为240像素
_btn_width = _image_width // 6  # 按钮宽度为屏幕宽度的1/6
_btn_height = _image_height // 7  # 按钮高度为屏幕高度的1/7

last_touch_read_time = time.ticks_ms()  # 初始化触摸屏读取时间，进行定时读取，避免占用太多资源
x = 0 #初始化触摸屏触摸点坐标
y = 0
pressed = False #是否触摸

# BUTTON1:创建 退出 按钮
exit_label = "<Exit"
size = image.string_size(exit_label)
exit_btn_pos = [0, 0,  _btn_width,  _btn_height] # [起始坐标x，起始坐标y，宽度w，高度h]
# BUTTON2：THRESH 按钮
thr_val_label = f"T{THRESH}"
thr_val_btn_pos = [0*_btn_width, 5*_btn_height, _btn_width, _btn_height]
# BUTTON3：STABLE_N 按钮
stable_val_label = f"S{STABLE_N}"
stable_val_btn_pos = [1*_btn_width, 5*_btn_height, _btn_width, _btn_height]

# ---------- 2. 平滑计数 ----------
cnt         = [0] * CLS_NUM      # 每类累积值
stable_cnt  = [0] * CLS_NUM      # 连续确认计数
stable_ok   = [False] * CLS_NUM  # 最终锁定位（可选）

# ---------- 3. 保存函数 ----------
def save_thresholds():
    with open(THRESHOLD_FILE, "w") as file:
        # ★ 删掉下面两行
        # file.write("red: " + str(red_thresholds) + "\n")
        # file.write("blue: " + str(blue_thresholds) + "\n")
        file.write(f"thresh: {THRESH}\n")
        file.write(f"stable: {STABLE_N}\n")
#判断触摸点是否再设定区域内
def is_in_button(x, y, btn_pos):
    return x > btn_pos[0] and x < btn_pos[0] + btn_pos[2] and y > btn_pos[1] and y < btn_pos[1] + btn_pos[3]        


while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th=0.5, iou_th=0.45)

    # 2.1 当前帧每类个数
    curr_num = [0] * CLS_NUM
    for obj in objs:
        if 0 <= obj.class_id < CLS_NUM:
            curr_num[obj.class_id] += 1

    # 2.2 更新平滑计数器
    for i in range(CLS_NUM):
        if curr_num[i]:
            cnt[i] += curr_num[i]
        else:
            cnt[i] *= DECAY
        cnt[i] = int(min(cnt[i], 300))

        # ---------- 新增：5 帧二次确认 ----------
        if cnt[i] >= THRESH and not stable_ok[i]:
            stable_cnt[i] += 1
            if stable_cnt[i] >= STABLE_N:
                stable_ok[i] = True        # 锁死该类结果
        else:
            stable_cnt[i] = 0              # 掉线就清零重来

    # ---------- 2.3 画检测框 ----------
    for obj in objs:
        cls = obj.class_id
        color = CLS_COLORS[cls % CLS_NUM]   # 取对应颜色
        img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=color)
        img.draw_string(obj.x, obj.y,
                        f'{labels[cls]}:{obj.score:.2f}',
                        color=color)

    # ---------- 2.4 显示 4 类数量 ----------
    y0 = 25
    for cls in range(CLS_NUM):
        disp_num = curr_num[cls] if stable_ok[cls] else 0
        img.draw_string(225, y0,
                        f'{labels[cls]}:{disp_num}',
                        CLS_COLORS[cls], scale=1)
        y0 += 18


#_________________________________________________________________________________________________________________ 
    # 检测触摸事件       
    current_time = time.ticks_ms()  # 每次循环开始时获取当前时间
    
    if current_time - last_touch_read_time >= 50: # 每50毫秒读取一次触摸屏
        last_touch_read_time = current_time # 更新触摸屏读取时间

        x, y, pressed = ts.read()  # 读取触摸屏事件
        x, y = image.resize_map_pos_reverse(img.width(), img.height(), disp.width(), disp.height(), image.Fit.FIT_CONTAIN, x, y) #xy映射校准
        
        if torch_flag == False and pressed: #触摸模拟按键消抖，认为抬起算一次触摸事件
            torch_flag = True
            torch_success = False
            print(x, y, pressed)
        if  pressed == False and torch_flag:
            torch_flag = False  
            torch_success = True
    img.draw_circle(x, y, 1, image.Color.from_rgb(255, 255, 255), 2) #显示点击位置

    # EXIT退出按键设计
    img.draw_string(8, 12, exit_label, image.Color.from_rgb(255, 0, 255))
    img.draw_rect(exit_btn_pos[0], exit_btn_pos[1], exit_btn_pos[2], exit_btn_pos[3],image.Color.from_rgb(255, 0, 255), 2)        
    if torch_success== True and is_in_button(x, y, exit_btn_pos):
        torch_success = False
        app.set_exit_flag(True)

    # ---- THRESH 按钮 ----
    img.draw_rect(thr_val_btn_pos[0], thr_val_btn_pos[1],
                  thr_val_btn_pos[2], thr_val_btn_pos[3],
                  image.Color.from_rgb(255,0,255), 2)
    img.draw_string(thr_val_btn_pos[0]+5, thr_val_btn_pos[1]+5,
                    f"T{THRESH}", image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, thr_val_btn_pos):
        torch_success = False
        # ★ 用简单方式调节：每点一次 +1，到 10 归 1
        THRESH = THRESH % 10 + 1
        save_thresholds()

    # ---- STABLE_N 按钮 ----
    img.draw_rect(stable_val_btn_pos[0], stable_val_btn_pos[1],
                  stable_val_btn_pos[2], stable_val_btn_pos[3],
                  image.Color.from_rgb(255,0,255), 2)
    img.draw_string(stable_val_btn_pos[0]+5, stable_val_btn_pos[1]+5,
                    f"S{STABLE_N}", image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, stable_val_btn_pos):
        torch_success = False
        # ★ 同理循环 1-10
        STABLE_N = STABLE_N % 10 + 1
        save_thresholds()


    # 2.5 FPS
    fps = time.fps()
    img.draw_string(240, 10, f"FPS{fps:.1f}",
                    image.Color.from_rgb(255, 255, 0), scale=1)
    disp.show(img)