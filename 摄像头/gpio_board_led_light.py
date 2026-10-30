from maix import gpio, pinmap, time,app

pinmap.set_pin_function("B3", "GPIOB3")
led = gpio.GPIO("GPIOB3", gpio.Mode.OUT)
led.value(0)

while not app.need_exit():
    
    for i in range(1,10000,1):
        led.toggle()
        time.sleep_ms(i)

