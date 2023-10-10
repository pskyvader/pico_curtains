import sys
from machine import Pin
from components import motor_control, led_control, button_control, webserver
from components.logger import log_message

interrupt = Pin(0, Pin.IN, Pin.PULL_DOWN)

if interrupt.value():
    sys.exit()

log_file = "mainlog.txt"
log_message("Starting the application", log_file)

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
        log_message(STOP_MESSAGE, log_file)
        motor_control_instance.stop_motor()
        led_control_instance.stop_blinking()
    else:
        log_message(START_MESSAGE, log_file)
        motor_control_instance.start_motor_up()
        led_control_instance.start_blinking()


def on_down_pressed():
    if motor_control_instance.is_motor_running():
        log_message(STOP_MESSAGE, log_file)
        motor_control_instance.stop_motor()
        led_control_instance.stop_blinking()
    else:
        log_message(START_MESSAGE, log_file)
        motor_control_instance.start_motor_down()
        led_control_instance.start_blinking()


def on_released():
    motor_control_instance.stop_motor()
    led_control_instance.stop_blinking()
    log_message(STOP_MESSAGE, log_file)


up_button.on_pressed = on_up_pressed
up_button.on_released = on_released

down_button.on_pressed = on_down_pressed
down_button.on_released = on_released

triggered_message = False
last_time = None
try:
    log_message("Start Webserver Loop", log_file)
    web_server.start_web_server_thread()
    log_message("Start Main Loop", log_file)
    while True:
        if interrupt.value():
            raise KeyboardInterrupt("interrupt pin")
        button_handler.check_buttons()
        running_time = motor_control_instance.get_running_time()
        if running_time > 15 * 1000:
            log_message("Motor run timeout", log_file)
            on_released()
        # if web_server.is_web_server_thread_running():
        last_request, last_request_time = web_server.get_last_request()
        if last_request != "" and last_request_time != last_time:
            last_time = last_request_time
            log_message("Last request" + last_request, log_file)
        # else:
        #     if not triggered_message:
        #         log_message("Web server thread is not running.", log_file)
        #         triggered_message = True
        #     # sys.exit()

except KeyboardInterrupt as e:
    log_message(e, log_file)
    sys.exit()
