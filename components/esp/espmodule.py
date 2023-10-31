from machine import UART, Pin
import time
from components.esp.errors import at_unknown, at_empty
from lib.logging import getLogger, handlers, StreamHandler
import gc


class ESPMODULE:
    line_separator = "\r" + "\n"
    log_file = "espmodule.txt"
    ESP8266_OK_STATUS = "OK" + line_separator
    ESP8266_ERROR_STATUS = "ERROR" + line_separator
    ESP8266_FAIL_STATUS = "FAIL" + line_separator
    ESP8266_BUSY_STATUS = "busy p..." + line_separator
    UART_TX_BUFFER_LENGTH = 1024
    UART_RX_BUFFER_LENGTH = 1024 * 2

    def __init__(self, uart_tx, uart_rx):
        self.logger = getLogger("espmodule")
        self.logger.addHandler(handlers.RotatingFileHandler(self.log_file))
        self.logger.addHandler(StreamHandler())
        self.ESP_UART_TX = uart_tx
        self.ESP_UART_RX = uart_rx

        self.uart = UART(
            1,
            baudrate=115200,
            tx=Pin(self.ESP_UART_TX),
            rx=Pin(self.ESP_UART_RX),
            txbuf=self.UART_TX_BUFFER_LENGTH,
            rxbuf=self.UART_RX_BUFFER_LENGTH,
            timeout=1000,
        )

    def _send_command(self, at_command):
        """
        Send an AT command to ESP8266 and receive its response.
        """
        self.logger.debug("AT command: %s", str(at_command))
        self.uart.write(at_command + self.line_separator)

    def _receive_command(self, timeout=10):
        response = bytes()
        start_time = time.time()

        while True:
            if self.uart.any() > 0:
                while self.uart.any() > 0:
                    # gc.collect()
                    self.logger.debug(
                        "ESP free: {} allocated: {}".format(
                            gc.mem_free(), gc.mem_alloc()
                        )
                    )
                    chunk = self.uart.read(self.UART_RX_BUFFER_LENGTH)
                    self.logger.debug("Received chunk, type: %s", type(chunk))
                    self.logger.debug(
                        "Receiving command chunk, content: %s", str(chunk)
                    )
                    response += chunk
                    # time.sleep(pause)
                break
            if time.time() - start_time > timeout:
                break
            # time.sleep(pause)
        self.logger.debug("AT response: %s", str(response))
        return response

    def _validate_response(self, response_str):
        if self.ESP8266_OK_STATUS in response_str:
            return response_str
        elif self.ESP8266_ERROR_STATUS in response_str:
            return response_str
        elif self.ESP8266_FAIL_STATUS in response_str:
            return response_str
        elif self.ESP8266_BUSY_STATUS in response_str:
            return self.ESP8266_BUSY_STATUS
        elif len(response_str) == 0:
            raise at_empty(str(response_str))
        else:
            raise at_unknown(str(response_str))

    def _send_and_receive_command(self, at_command, attempts=10):
        self._send_command(at_command)

        step = 0
        while step < attempts:
            try:
                self.logger.debug("send command and receive command")
                response = self._receive_command()
            except Exception as e:
                self.logger.error("Send and receive error: %s", str(e))
                return self.ESP8266_ERROR_STATUS
            try:
                self.logger.debug("receive command")
                response_str = self._validate_response(response)
            except Exception as e:
                self.logger.error("Validation error: %s", str(e))
                return self.ESP8266_ERROR_STATUS

            if response_str == self.ESP8266_BUSY_STATUS:
                step += 1
                continue
            return response_str
        return self.ESP8266_ERROR_STATUS
