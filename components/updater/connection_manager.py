from machine import Timer
import time
import sys
from components.logger import log_message


def waiting_message(esp_process, timeout_seconds, start_time, times=0):
    if (
        esp_process.is_initialized() is None
        and time.time() - start_time < timeout_seconds
    ):
        sys.stdout.write("Waiting for ESP initialization... [" + "=" * times)
        sys.stdout.write("]\r")
        timer = Timer()
        timer.init(
            period=500,
            mode=Timer.ONE_SHOT,
            callback=lambda t: waiting_message(
                esp_process, timeout_seconds, start_time, times + 1
            ),
        )


def connect_process(esp_process, log_file, attempt=0):
    timeout_seconds = 30
    esp_process.initialized = None
    if esp_process.is_wifi_connected():
        log_message("ESP already connected", log_file)
        esp_process.initialized = True
        ip = esp_process.get_ip()
        log_message("IP:" + ip, log_file)
        return

    start_time = time.time()
    waiting_message(esp_process, timeout_seconds, start_time)
    if attempt == 0:
        esp_process.start()
    else:
        esp_process.connect_to_wifi()
    if not esp_process.is_initialized():
        log_message("ESP initialization failed", log_file)
        if attempt < 3:
            log_message("Retry", log_file)
            connect_process(esp_process, log_file, attempt + 1)
        else:
            return False
    else:
        log_message("ESP initialization succeeded", log_file)
        ip = esp_process.get_ip()
        log_message("IP:" + ip, log_file)
