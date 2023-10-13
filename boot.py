import sys
from components.updater.updater import updater
from machine import Pin
from components.led_control import LEDControl
from components.logger import log_message


interrupt = Pin(0, Pin.IN, Pin.PULL_DOWN)
log_file = "log.txt"
led_control_instance = LEDControl(25)


def boot():
    log_message("Starting the application", log_file)
    led_control_instance.start_blinking()
    update_instance = updater(
        wifi_ssid="Pabloysofi",
        wifi_pass="jaimitoelperrito",
        update_url="http://192.168.1.231/",
        update_port=3000,
        uart_tx=4,
        uart_rx=5,
    )
    update_instance.start_update()
    led_control_instance.stop_blinking()
    log_message("Application completed", log_file)


try:
    if interrupt.value():
        raise KeyboardInterrupt("interrupt pin")
    boot()
except KeyboardInterrupt as e:
    print(e)
    log_message("Application Interrupted", log_file)
    sys.exit()
