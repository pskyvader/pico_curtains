from components.esp.web_client import web_client
from components.logger import log_message
from machine import Timer
import time
import sys


class updater:
    log_file = "updater_log.txt"
    continue_program = True
    timeout_seconds = 30
    start_time = time.time()

    def __init__(
        self, wifi_ssid, wifi_pass, update_url, update_port=80, uart_tx=4, uart_rx=5
    ) -> None:
        self.update_url = update_url
        self.update_port = update_port
        self.esp_process = web_client(
            wifi_ssid=wifi_ssid, wifi_pass=wifi_pass, uart_tx=uart_tx, uart_rx=uart_rx
        )

    def stop_update(self):
        self.continue_program = False

    def waiting_message(self, times=0):
        if (
            self.continue_program
            and self.esp_process.is_initialized() is None
            and time.time() - self.start_time < self.timeout_seconds
        ):
            sys.stdout.write("Waiting for ESP initialization... [" + "=" * times)
            sys.stdout.write("]\r")  # Move cursor back to the beginning of the line

            timer = Timer()
            timer.init(
                period=500,
                mode=Timer.ONE_SHOT,
                callback=lambda t: self.waiting_message(times + 1),
            )

    def connect_process(self, attempt=0):
        self.esp_process.initialized = None
        if self.esp_process.is_wifi_connected():
            log_message("ESP already connected", self.log_file)
            self.esp_process.initialized = True
            ip = self.esp_process.get_ip()
            log_message("IP:" + ip, self.log_file)
            return

        self.waiting_message()
        if attempt == 0:
            self.esp_process.start()
        else:
            self.esp_process.connect_to_wifi()
        if not self.esp_process.is_initialized():
            log_message("ESP initialization failed", self.log_file)
            if self.continue_program and attempt < 3:
                log_message("Retry", self.log_file)
                self.connect_process(attempt + 1)
            else:
                return False
        else:
            log_message("ESP initialization succeeded", self.log_file)
            ip = self.esp_process.get_ip()
            log_message("IP:" + ip, self.log_file)

    def start_update(self):
        self.connect_process()
        if self.esp_process.is_initialized():
            # url = "http://www.httpbin.org/ip"
            # url = "http://www.google.com/"
            # url = "http://192.168.1.86:3000"
            url = self.update_url
            port = self.update_port
            (header, body, status_code) = self.esp_process.get_url_response(url, port)
            # log_message("Status Code: " + str(status_code), self.log_file)
            # log_message("Header: " + str(header), self.log_file)
            # log_message("Body: ", self.log_file)
            # log_message(body, self.log_file)

            matches = [match for match in body if "version.json" in match]
            if len(matches) > 0:
                (header, body, status_code) = self.esp_process.get_url_response(
                    url + "version.json", port
                )
                if body and body["version"]:
                    log_message("Version: " + str(body["version"]), self.log_file)
                # log_message("Version Status Code: " + str(status_code), self.log_file)
                # log_message("Version Header: " + str(header), self.log_file)
                # log_message("Version Body: ", self.log_file)
                # log_message(body, self.log_file)
