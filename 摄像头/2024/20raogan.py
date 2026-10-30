from maix import camera, display, image, nn, app, time,uart,touchscreen

detector = nn.YOLO11(model="/root/models/my_model1/yolo11s_int8.mud", dual_buff=True)

# cam = camera.Camera(detector.input_width(), detector.input_height(), detector.input_format())
#鎽勫儚澶撮厤缃�
disp = display.Display()
cam = camera.Camera(320, 240,fps=60)   #QVGA,fps涔熷彲閫�80
# cam = camera.Camera(160, 120,fps=60)   #QQVGA,fps涔熷彲閫�80
disp.set_backlight(40)  #璁剧疆鑳屽厜浜�搴�(0-100)
cam.awb_mode(0)		    # 0,寮€鍚�鐧藉钩琛�;1,鍏抽棴鐧藉钩琛�
cam.exp_mode(0)         #璁剧疆涓鸿嚜鍔ㄦ洕鍏�
# cam.gain(10)           #璁剧疆澧炵泭(娉ㄦ剰璁剧疆澧炵泭鍚庯紝鎽勫儚澶翠細鍒囨崲鍒版墜鍔ㄦ洕鍏夋ā寮�)
# cam.exposure(550)      #璁剧疆鏇濆厜鏃堕棿(娉ㄦ剰璁剧疆鏇濆厜鏃堕棿鍚庯紝鎽勫儚澶翠細鍒囨崲鍒版墜鍔ㄦ洕鍏夋ā寮�)
cam.luma(40)		    # 璁剧疆浜�搴︼紝鑼冨洿[0, 100]
cam.constrast(50)		# 璁剧疆瀵规瘮搴︼紝鑼冨洿[0, 100]
cam.saturation(50)		# 璁剧疆楗卞拰搴︼紝鑼冨洿[0, 100]
cam.skip_frames(30)     # 璺宠繃寮€澶寸殑30甯э紝璁╃浉鏈哄浘鍍忓湪鏀瑰彉鐩告満璁剧疆鍚庣ǔ瀹氫笅鏉�
#涓插彛閰嶇疆鍙婄浉鍏冲弬鏁�
device = "/dev/ttyS0" #閫夋嫨USB寮曞嚭鐨勪覆鍙�
serial = uart.UART(device, 115200) #璁剧疆涓插彛娉㈢壒鐜�

# 甯х巼璁＄畻鐩稿叧鍙傛暟
fps = 0
last_time = time.time()
frame_count = 0
# 瑙︽懜灞忛厤缃� 鍙� 鐩稿叧瑙︽懜鍙傛暟
ts = touchscreen.TouchScreen() 
torch_flag = False
torch_success = False #鏉炬墜鎶�璧凤紝璇ユ爣蹇椾綅缃�1
# 灞忓箷瀹藉害鍜岄珮搴�
_image_width = 320  # 瀹氫箟鍥惧儚瀹藉害涓�320鍍忕礌
_image_height = 240  # 瀹氫箟鍥惧儚楂樺害涓�240鍍忕礌
_btn_width = _image_width // 6  # 鎸夐挳瀹藉害涓哄睆骞曞�藉害鐨�1/6
_btn_height = _image_height // 7  # 鎸夐挳楂樺害涓哄睆骞曢珮搴︾殑1/7

# BUTTON1:鍒涘缓 閫€鍑� 鎸夐挳
exit_label = "<Exit"
size = image.string_size(exit_label)
exit_btn_pos = [0, 0,  _btn_width,  _btn_height] # [璧峰�嬪潗鏍噚锛岃捣濮嬪潗鏍噛锛屽�藉害w锛岄珮搴�h]

#鐢ㄦ埛鑷�瀹氫箟鍙橀噺鍒濆�嬪寲
red_center = None
green_center = None 
delta_x_red = 0   
delta_x_green = 0 


#鍒ゆ柇瑙︽懜鐐规槸鍚﹀啀璁惧畾鍖哄煙鍐�
def is_in_button(x, y, btn_pos):
    return x > btn_pos[0] and x < btn_pos[0] + btn_pos[2] and y > btn_pos[1] and y < btn_pos[1] + btn_pos[3]

while not app.need_exit():
    img = cam.read()
    objs = detector.detect(img, conf_th = 0.5, iou_th = 0.45)

    red_center = None
    green_center = None

    for obj in objs:
        img.draw_rect(obj.x, obj.y, obj.w, obj.h, color=image.COLOR_RED)
        msg = f'{detector.labels[obj.class_id]}: {obj.score:.2f}'
        img.draw_string(obj.x, obj.y, msg, color=image.COLOR_RED)

        label = detector.labels[obj.class_id].lower()
        cx = obj.x + obj.w // 2
        cy = obj.y + obj.h // 2

        if 'red' in label:
            red_center = (cx, cy)
            delta_x_red = red_center[0] #鑼冨洿鏄犲皠鍒�0 - 320
            img.draw_circle(cx, cy, 5, color=image.COLOR_RED)
            img.draw_string(cx - 10, cy - 15, "RED", color=image.COLOR_RED)
        elif 'green' in label:
            green_center = (cx, cy)
            delta_x_green = green_center[0] #鑼冨洿鏄犲皠鍒�0 - 320
            img.draw_circle(cx, cy, 5, color=image.COLOR_GREEN)
            img.draw_string(cx - 15, cy - 15, "GREEN", color=image.COLOR_GREEN)

    img.draw_string(240, 20, f"Red {delta_x_red:d}", image.Color.from_rgb(0, 255, 255), scale=1)
    img.draw_string(240, 30, f"Gre {delta_x_green:d}", image.Color.from_rgb(0, 255, 255), scale=1)    

#_________________________________________________________________________________________________________________ 
    # 妫€娴嬭Е鎽镐簨浠�
    x, y, pressed = ts.read()  # 璇诲彇瑙︽懜灞忎簨浠�
    x, y = image.resize_map_pos_reverse(img.width(), img.height(), disp.width(), disp.height(), image.Fit.FIT_CONTAIN, x, y) #xy鏄犲皠鏍″噯
    img.draw_circle(x, y, 1, image.Color.from_rgb(255, 255, 255), 2) #鏄剧ず鐐瑰嚮浣嶇疆
    if torch_flag == False and pressed: #瑙︽懜妯℃嫙鎸夐敭娑堟姈锛岃�や负鎶�璧风畻涓€娆¤Е鎽镐簨浠�
        torch_flag = True
        torch_success = False
        print(x, y, pressed)
    if  pressed == False and torch_flag:
        torch_flag = False  
        torch_success = True


    # EXIT閫€鍑烘寜閿�璁捐��
    img.draw_string(8, 12, exit_label, image.Color.from_rgb(255, 0, 255))
    img.draw_rect(exit_btn_pos[0], exit_btn_pos[1], exit_btn_pos[2], exit_btn_pos[3],image.Color.from_rgb(255, 0, 255), 2)        
    if torch_success== True and is_in_button(x, y, exit_btn_pos):
        torch_success = False
        app.set_exit_flag(True)

#_________________________________________________________________________________________________________________ 
    # 璁＄畻甯х巼
    frame_count += 1
    current_time = time.time()
    elapsed_time = current_time - last_time
    if elapsed_time >= 1.0:
        fps = frame_count / elapsed_time
        frame_count = 0
        last_time = current_time
        # print(f"Frame Rate: {fps:.2f} FPS")
    img.draw_string(240, 10, f"FPS{fps:.1f}", image.Color.from_rgb(255, 255, 0), scale=1)# 鍦ㄥ浘鍍忎笂缁樺埗甯х巼淇℃伅

#_________________________________________________________________________________________________________________        
    # 鏄剧ず澶勭悊鍚庣殑鍥惧儚
    disp.show(img)