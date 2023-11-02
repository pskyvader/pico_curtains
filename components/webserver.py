from components.esp.web_server import web_server
import _thread
import time
from machine import Pin
from lib.logging import getLogger, handlers, StreamHandler

STOP_MESSAGE = "motor stopped"
START_MESSAGE = "motor running"

interrupt = Pin(0, Pin.IN, Pin.PULL_DOWN)


class WebServer:
    log_file = "webserver.txt"

    def __init__(self, motor_control_instance, led_control_instance):
        self.motor_control_instance = motor_control_instance
        self.led_control_instance = led_control_instance
        self.thread_id = None  # Store the thread ID
        self.esp_process = web_server(
            wifi_ssid="Pabloysofi", wifi_pass="jaimitoelperrito", uart_tx=4, uart_rx=5
        )
        self.last_request = ""
        self.last_request_time = time.time()
        self.logger = getLogger("webserver")
        self.logger.addHandler(handlers.RotatingFileHandler(self.log_file))
        self.logger.addHandler(StreamHandler())

    def on_up_pressed(self):
        if self.motor_control_instance.is_motor_running():
            self.logger.info(STOP_MESSAGE)
            self.motor_control_instance.stop_motor()
            self.led_control_instance.stop_blinking()
        else:
            self.logger.info(START_MESSAGE)
            self.motor_control_instance.start_motor_up()
            self.led_control_instance.start_blinking()

    def on_down_pressed(self):
        if self.motor_control_instance.is_motor_running():
            self.logger.info(STOP_MESSAGE)
            self.motor_control_instance.stop_motor()
            self.led_control_instance.stop_blinking()
        else:
            self.logger.info(START_MESSAGE)
            self.motor_control_instance.start_motor_down()
            self.led_control_instance.start_blinking()

    def start_web_server(self):
        if self.esp_process.start_web_server(80):
            self.logger.info("Web server started on port 80.")
            return True

        self.logger.error("Failed to start the web server.")
        return False

    def start_web_server_thread(self):
        wifi_connected = self.esp_process.is_wifi_connected()
        self.led_control_instance.set_led_state(wifi_connected)
        if not wifi_connected:
            self.logger.error("Wifi not available")
            return False
        webserver_started = self.start_web_server()

        if webserver_started:
            self.logger.debug("try to start threaded server")
            self.thread_id = _thread.start_new_thread(self.handle_requests, ())
            self.logger.info("threaded server started: " + str(self.thread_id))
            return True
        else:
            self.logger.error("Webserver not started")
            return False

    def is_web_server_thread_running(self):
        # Check if the web server thread is running
        if self.thread_id is not None:
            return True
        return False

    def get_last_request(self):
        return self.last_request, self.last_request_time

    def handle_requests(self):
        thread_log_file = "webserver_thread.txt"
        logger = getLogger("webserver_thread")
        logger.addHandler(handlers.RotatingFileHandler(thread_log_file))

        try:
            while True:
                if interrupt.value():
                    raise KeyboardInterrupt("interrupt pin")
                if not self.led_control_instance.is_blinking:
                    self.led_control_instance.start_blinking()
                # else:
                #     self.led_control_instance.stop_blinking()
                headers, request_body, conn_id = self.esp_process.handle_web_request()
                if headers is None:
                    if request_body is not None:
                        logger.error(
                            "Webserver error:" + str(request_body), thread_log_file
                        )
                    continue

                self.last_request = str(headers)
                self.last_request_time = time.time()
                # log_message("Request: " + self.last_request, thread_log_file)
                if headers.startswith("GET /up"):
                    self.on_up_pressed()
                    self.esp_process.send_ok_response(conn_id)
                elif headers.startswith("GET /down"):
                    self.on_down_pressed()
                    self.esp_process.send_ok_response(conn_id)
                elif headers.startswith("GET / "):
                    file_path = "/html/index.html"
                    self.esp_process.send_web_file(conn_id, file_path)
                else:
                    self.esp_process.send_404_response(conn_id)

        except KeyboardInterrupt as e:
            logger.exception(e)
            self.led_control_instance.stop_blinking()
            _thread.exit()
