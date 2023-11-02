import sys
from components.updater.updater import updater
from machine import Pin
from components.led_control import LEDControl
from lib.logging import getLogger, handlers, basicConfig, INFO, StreamHandler


interrupt = Pin(0, Pin.IN, Pin.PULL_DOWN)
led_control_instance = LEDControl(25)

basicConfig(level=INFO)

log_file = "boot.txt"
logger_boot = getLogger("boot")
logger_boot.addHandler(handlers.RotatingFileHandler(log_file))
logger_boot.addHandler(StreamHandler())


def boot():
    logger_boot.info("Starting the application on Boot")
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
    logger_boot.info("Application completed")


try:
    if interrupt.value():
        raise KeyboardInterrupt("interrupt pin")
    boot()
except KeyboardInterrupt as e:
    logger_boot.exception("Application Interrupted:" + str(e))
    sys.exit()
