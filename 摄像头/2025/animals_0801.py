from maix import camera, display, image, touchscreen, app, time, nn
from maix import uart
import os, math

# ---------- 0. 参数 ----------
THRESH  = 4
STABLE_N = 2
THRESHOLD_FILE = "/mnt/data/my_thresholds.txt"
ROI_FILE       = "/mnt/data/my_roi.txt"

# 阈值
try:
    with open(THRESHOLD_FILE, "r") as f:
        for ln in f:
            ln = ln.strip()
            if ln.startswith("thresh:"):
                THRESH = int(ln.split(":")[1])
            elif ln.startswith("stable:"):
                STABLE_N = int(ln.split(":")[1])
except Exception:
    pass

# ---------- ROI ----------
DEFAULT_ROI = [0, 0, 240, 240]   # [x, y, w, h]
roi = DEFAULT_ROI[:]
try:
    with open(ROI_FILE, "r") as f:
        roi = [int(v) for v in f.readline().strip().split(",")]
except Exception:
    pass
def save_roi():
    with open(ROI_FILE, "w") as f:
        f.write(",".join(map(str, roi)))

# ---------- 模型 ----------
detector = nn.YOLO11(model="/root/models/my_model5/yolo11s_int8.mud", dual_buff=True)   #YOLO11S
# detector = nn.YOLO11(model="/root/models/my_model4/yolo11n_int8.mud", dual_buff=True)   #YOLO11N
labels  = ["kongque", "lang", "hou", "hu", "xiang"]
CLS_NUM = len(labels)
CLS_COLORS = [
    image.COLOR_RED,
    image.COLOR_BLUE,
    image.COLOR_GREEN,
    image.COLOR_YELLOW,
    image.Color.from_rgb(255, 165, 0)
]
DECAY = 0.5

# ---------- 硬件 ----------
disp = display.Display()
cam  = camera.Camera(240, 240, fps=60)
disp.set_backlight(40)
cam.awb_mode(0)
cam.exp_mode(0)
cam.luma(40)
cam.constrast(50)
cam.saturation(50)
cam.skip_frames(30)
serial = uart.UART("/dev/ttyS0", 115200)
ts = touchscreen.TouchScreen()

# ---------- 按钮 ----------
_image_width  = 240
_image_height = 240
_btn_width    = _image_width // 4
_btn_height   = _image_height // 7
last_touch_read_time = time.ticks_ms()
x = y = 0
pressed = False
torch_flag   = False
torch_success = False

exit_label      = "<Exit"
exit_btn_pos    = [0, 0, _btn_width, _btn_height]

thr_val_label   = f"T{THRESH}"
thr_val_btn_pos = [0*_btn_width, 5*_btn_height, _btn_width, _btn_height]

stable_val_label   = f"S{STABLE_N}"
stable_val_btn_pos = [1*_btn_width, 5*_btn_height, _btn_width, _btn_height]

# ROI 同步调节按钮
btn_roi_size = [2*_btn_width, 5*_btn_height, _btn_width*2, _btn_height]
roi_step = 5

# ---------- 计数 ----------
cnt        = [0] * CLS_NUM
stable_cnt = [0] * CLS_NUM
stable_ok  = [False] * CLS_NUM

# ---------- 工具 ----------
def save_thresholds():
    with open(THRESHOLD_FILE, "w") as file:
        file.write(f"thresh: {THRESH}\n")
        file.write(f"stable: {STABLE_N}\n")

def is_in_button(x, y, btn_pos):
    return x > btn_pos[0] and x < btn_pos[0] + btn_pos[2] and y > btn_pos[1] and y < btn_pos[1] + btn_pos[3]

# ---------- 主循环 ----------
while not app.need_exit():
    img = cam.read()

    # 裁剪 ROI 并检测
    roi_img = img.crop(roi[0], roi[1], roi[2], roi[3])
    objs = detector.detect(roi_img, conf_th=0.7, iou_th=0.65)

    # 计数
    curr_num = [0] * CLS_NUM
    for obj in objs:
        if 0 <= obj.class_id < CLS_NUM:
            curr_num[obj.class_id] += 1
    for i in range(CLS_NUM):
        if curr_num[i]:
            cnt[i] += curr_num[i]
        else:
            cnt[i] *= DECAY
        cnt[i] = int(min(cnt[i], 300))
        if cnt[i] >= THRESH and not stable_ok[i]:
            stable_cnt[i] += 1
            if stable_cnt[i] >= STABLE_N:
                stable_ok[i] = True
        else:
            stable_cnt[i] = 0

    # 画框
    for obj in objs:
        cls = obj.class_id
        color = CLS_COLORS[cls % CLS_NUM]
        abs_x = roi[0] + obj.x
        abs_y = roi[1] + obj.y
        img.draw_rect(abs_x, abs_y, obj.w, obj.h, color=color)
        img.draw_string(abs_x, abs_y, f'{labels[cls]}:{obj.score:.2f}', color=color)

    # 显示类别数量
    y0 = 25
    for cls in range(CLS_NUM):
        disp_num = curr_num[cls] if stable_ok[cls] else 0
        img.draw_string(150, y0, f'{labels[cls]}:{disp_num}', CLS_COLORS[cls], scale=1)
        y0 += 15

    # 触摸读取（你原来的写法，映射正确）
    current_time = time.ticks_ms()
    if current_time - last_touch_read_time >= 50:
        last_touch_read_time = current_time
        x, y, pressed = ts.read()
        x, y = image.resize_map_pos_reverse(img.width(), img.height(), disp.width(), disp.height(), image.Fit.FIT_CONTAIN, x, y)
        if torch_flag == False and pressed:
            torch_flag = True
            torch_success = False
        if pressed == False and torch_flag:
            torch_flag = False
            torch_success = True
    img.draw_circle(x, y, 1, image.Color.from_rgb(255, 255, 255), 2)

    # 按钮：Exit / T / S / ROI
    img.draw_string(8, 12, exit_label, image.Color.from_rgb(255, 0, 255))
    img.draw_rect(exit_btn_pos[0], exit_btn_pos[1], exit_btn_pos[2], exit_btn_pos[3], image.Color.from_rgb(255, 0, 255), 2)
    if torch_success and is_in_button(x, y, exit_btn_pos):
        torch_success = False
        app.set_exit_flag(True)

    img.draw_rect(thr_val_btn_pos[0], thr_val_btn_pos[1], thr_val_btn_pos[2], thr_val_btn_pos[3], image.Color.from_rgb(255,0,255), 2)
    img.draw_string(thr_val_btn_pos[0]+5, thr_val_btn_pos[1]+5, f"T{THRESH}", image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, thr_val_btn_pos):
        torch_success = False
        THRESH = THRESH % 10 + 1
        save_thresholds()

    img.draw_rect(stable_val_btn_pos[0], stable_val_btn_pos[1], stable_val_btn_pos[2], stable_val_btn_pos[3], image.Color.from_rgb(255,0,255), 2)
    img.draw_string(stable_val_btn_pos[0]+5, stable_val_btn_pos[1]+5, f"S{STABLE_N}", image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, stable_val_btn_pos):
        torch_success = False
        STABLE_N = STABLE_N % 10 + 1
        save_thresholds()

    # ROI 调节按钮（宽高同步）
    size_str = f"ROI:{roi[2]}"
    img.draw_rect(*btn_roi_size, image.Color.from_rgb(0,255,255), 2)
    img.draw_string(btn_roi_size[0]+5, btn_roi_size[1]+5, size_str, image.Color.from_rgb(255,255,0), scale=1)
    if torch_success and is_in_button(x, y, btn_roi_size):
        torch_success = False
        new_size = roi[2] + roi_step
        if new_size > 240:
            new_size = 180
        roi[2] = roi[3] = new_size
        roi[0] = roi[1] = (240 - new_size) // 2
        save_roi()

    # 画 ROI 框
    img.draw_rect(roi[0], roi[1], roi[2], roi[3], image.Color.from_rgb(0, 255, 255), 2)

    # FPS
    fps = time.fps()
    img.draw_string(160, 10, f"FPS{fps:.1f}", image.Color.from_rgb(255, 255, 0), scale=1)
    disp.show(img)