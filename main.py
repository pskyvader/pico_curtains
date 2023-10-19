import sys
from machine import Pin
from components import motor_control, led_control, button_control, webserver
from lib.logging import getLogger, handlers, basicConfig, ERROR, StreamHandler


basicConfig(level=ERROR, stream=sys.stdout)
log_file = "main.txt"
logger_main = getLogger("main")
logger_main.addHandler(handlers.RotatingFileHandler(log_file))
logger_main.addHandler(StreamHandler())


interrupt = Pin(0, Pin.IN, Pin.PULL_DOWN)

if interrupt.value():
    sys.exit()

logger_main.info("Starting the application")

button_handler = button_control.ButtonController()
motor_control_instance = motor_control.MotorControl(20, 21)


led_control_instance = led_control.LEDControl(25)

# Add buttons to the controller
up_button = button_handler.add_button(pin=16, name="UpButton")
down_button = button_handler.add_button(pin=17, name="DownButton")


STOP_MESSAGE = "motor stopped"
START_MESSAGE = "motor running"

web_server = webserver.WebServer(
    motor_control_instance,
    led_control_instance,
)


# Set event handlers for button presses, releases, and holds
def on_up_pressed():
    if motor_control_instance.is_motor_running():
        logger_main.info(STOP_MESSAGE)
        motor_control_instance.stop_motor()
        led_control_instance.stop_blinking()
    else:
        logger_main.info(START_MESSAGE)
        motor_control_instance.start_motor_up()
        led_control_instance.start_blinking()
    return True


def on_down_pressed():
    if motor_control_instance.is_motor_running():
        logger_main.info(STOP_MESSAGE)
        motor_control_instance.stop_motor()
        led_control_instance.stop_blinking()
    else:
        logger_main.info(START_MESSAGE)
        motor_control_instance.start_motor_down()
        led_control_instance.start_blinking()


def on_released():
    motor_control_instance.stop_motor()
    led_control_instance.stop_blinking()
    logger_main.info(STOP_MESSAGE)


up_button.on_pressed = on_up_pressed
up_button.on_released = on_released

down_button.on_pressed = on_down_pressed
down_button.on_released = on_released

triggered_message = False
last_time = None
try:
    logger_main.info("Start Webserver Loop")
    web_server.start_web_server_thread()
    logger_main.info("Start Main Loop")
    while True:
        if interrupt.value():
            raise KeyboardInterrupt("interrupt pin")
        button_handler.check_buttons()
        running_time = motor_control_instance.get_running_time()
        if running_time > 15 * 1000:
            logger_main.debug("Motor run timeout")
            on_released()
        # if web_server.is_web_server_thread_running():
        last_request, last_request_time = web_server.get_last_request()
        if last_request != "" and last_request_time != last_time:
            last_time = last_request_time
            logger_main.info("Last request" + last_request)
        # else:
        #     if not triggered_message:
        #         log_message("Web server thread is not running.")
        #         triggered_message = True
        #     # sys.exit()

except KeyboardInterrupt as e:
    logger_main.exception(str(e))
    sys.exit()
