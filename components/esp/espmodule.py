from machine import UART, Pin
import time
from components.logger import log_message  # Import the logger
from components.esp.errors import at_unknown, at_empty


# Define a log file name
log_file = "espmodule.txt"


class ESPMODULE:
    ESP8266_OK_STATUS = "OK\r\n"
    ESP8266_ERROR_STATUS = "ERROR\r\n"
    ESP8266_FAIL_STATUS = "FAIL\r\n"
    ESP8266_BUSY_STATUS = "busy p...\r\n"
    UART_TX_BUFFER_LENGTH = 1024
    UART_RX_BUFFER_LENGTH = 1024 * 2

    def __init__(self, uart_tx, uart_rx):
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
        # log_message("AT command: " + at_command, log_file)
        log_message("AT command: " + str(at_command), log_file)
        self.uart.write(at_command + "\r\n")

    def _receive_command(self, pause=1, timeout=10):
        response = bytes()
        start_time = time.time()

        while True:
            if self.uart.any() > 0:
                while self.uart.any() > 0:
                    chunk = self.uart.read(self.UART_RX_BUFFER_LENGTH)
                    log_message("Receiving command: " + str(chunk), log_file)
                    response += chunk
                    time.sleep(pause)
                break
            if time.time() - start_time > timeout:
                break  # Exit the loop on timeout
            time.sleep(pause)

        log_message("AT response: " + str(response), log_file)
        return response

    def _parse_response(self, response_str):
        if self.ESP8266_OK_STATUS in response_str:
            return response_str
        elif self.ESP8266_ERROR_STATUS in response_str:
            return response_str
        elif self.ESP8266_FAIL_STATUS in response_str:
            return response_str
        elif self.ESP8266_BUSY_STATUS in response_str:
            return self.ESP8266_BUSY_STATUS
        elif len(response_str) == 0:
            return at_empty(str(response_str))
        else:
            raise at_unknown(str(response_str))

    def _send_and_receive_command(self, at_command, delay=1, attempts=10):
        self._send_command(at_command)

        step = 0
        while step < attempts:
            response = self._receive_command(pause=delay, timeout=attempts)
            response_str = self._parse_response(response)
            if response_str == self.ESP8266_BUSY_STATUS:
                step += 1
                continue
            return response_str
        return None
