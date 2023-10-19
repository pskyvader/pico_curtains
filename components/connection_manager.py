from machine import Timer
import time
import sys
from lib.logging import getLogger, handlers, StreamHandler


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
    return None


def connect_process(esp_process, attempt=0, logger_connection_manager=None):
    if logger_connection_manager is None:
        log_file = "connection_manager.txt"

        logger_connection_manager = getLogger("connection_manager")
        logger_connection_manager.addHandler(handlers.RotatingFileHandler(log_file))
        logger_connection_manager.addHandler(StreamHandler())

    timeout_seconds = 30
    esp_process.initialized = None
    if attempt == 0 and esp_process.is_wifi_connected():
        logger_connection_manager.info("ESP already connected")
        esp_process.initialized = True
        ip = esp_process.get_ip()
        logger_connection_manager.info("IP:" + ip)
        return True
    if attempt == 0:
        start_time = time.time()
        waiting_message(esp_process, timeout_seconds, start_time)

    esp_process.start()
    if not esp_process.is_initialized():
        logger_connection_manager.error("ESP initialization failed")
        if attempt < 3:
            logger_connection_manager.info("Retry:" + str(attempt + 1) + "/3")
            return connect_process(esp_process, attempt + 1, logger_connection_manager)
        else:
            logger_connection_manager.critical("Max retries reached.")
            return False
    else:
        logger_connection_manager.info("ESP initialization succeeded")
        ip = esp_process.get_ip()
        logger_connection_manager.info("IP:" + ip)
        return True
