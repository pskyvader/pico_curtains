import ure

from components.esp.espmodule import ESPMODULE
from components.esp.errors import (
    http_connection_fail,
    http_command_fail,
    http_response_invalid,
    at_set,
)
from components.esp.response_parser import response_parser
from lib.logging import getLogger, handlers, StreamHandler


class wifi_module(ESPMODULE):
    line_separator = "\r" + "\n"
    # line_separator = ""
    ESP8266_WIFI_CONNECTED = "WIFI CONNECTED"
    ESP8266_WIFI_GOT_IP_CONNECTED = "WIFI GOT IP"
    ESP8266_WIFI_DISCONNECTED = "WIFI DISCONNECT"
    ESP8266_WIFI_AP_NOT_PRESENT = "WIFI AP NOT FOUND"
    ESP8266_WIFI_AP_WRONG_PWD = "WIFI AP WRONG PASSWORD"
    log_file = "espwifilog.txt"

    def __init__(self, wifi_ssid, wifi_pass, uart_tx, uart_rx, baudrate=None):
        super().__init__(uart_tx, uart_rx, baudrate)
        self.WIFI_SSID = wifi_ssid
        self.WIFI_PASS = wifi_pass
        self.initialized = None  # Use None to indicate not yet initialized
        self.logger_wifi_module = getLogger("wifi_module")
        self.logger_wifi_module.addHandler(handlers.RotatingFileHandler(self.log_file))
        self.logger_wifi_module.addHandler(StreamHandler())
        self.parser = response_parser()

    def pre_connect(self):
        try:
            mode = 3
            tx_data = "AT+CWMODE_CUR=" + str(mode)
            ret_data = self._send_and_receive_command(tx_data)
            if ret_data == None or self.ESP8266_OK_STATUS not in ret_data:
                return False

            ret_data = self._send_and_receive_command("ATE0")
            if ret_data == None or self.ESP8266_OK_STATUS not in ret_data:
                return False
        except Exception as e:
            self.logger_wifi_module.error("Pre connect error: " + str(e))
            return False

        self.logger_wifi_module.info("Pre connect succeeded")
        return True

    def connect_to_wifi(self):
        tx_data = (
            "AT+CWJAP_CUR="
            + '"'
            + self.WIFI_SSID
            + '"'
            + ","
            + '"'
            + self.WIFI_PASS
            + '"'
            + ""
        )
        self.initialized = False

        try:
            ret_data = self._send_and_receive_command(tx_data)
        except Exception as e:
            self.logger_wifi_module.exception(str(e))
            return None

        if self.ESP8266_WIFI_CONNECTED in ret_data:
            if self.ESP8266_WIFI_GOT_IP_CONNECTED in ret_data:
                self.initialized = True
                return self.ESP8266_WIFI_CONNECTED
            return self.ESP8266_WIFI_DISCONNECTED

        if "+CWJAP" in ret_data:
            if "1" in ret_data:
                return self.ESP8266_WIFI_DISCONNECTED
            elif "2" in ret_data:
                return self.ESP8266_WIFI_AP_WRONG_PWD
            elif "3" in ret_data:
                return self.ESP8266_WIFI_AP_NOT_PRESENT
            elif "4" in ret_data:
                return self.ESP8266_WIFI_DISCONNECTED
            else:
                return None
        else:
            return self.ESP8266_WIFI_DISCONNECTED

    def is_initialized(self):
        return self.initialized

    def is_wifi_connected(self):
        self.logger_wifi_module.debug("Checking Wi-Fi connection...")
        tx_data = "AT+CWJAP?"
        try:
            ret_data = self._send_and_receive_command(tx_data)
            if (
                ret_data
                and self.ESP8266_OK_STATUS in ret_data
                and "+CWJAP:" in ret_data
            ):
                return True
        except Exception as e:
            self.logger_wifi_module.exception(str(e))

        self.logger_wifi_module.error("Wi-Fi is not connected")
        return False

    def start(self):
        self.logger_wifi_module.info("Initialize ESP...")
        preconnect = self.pre_connect()
        if not preconnect:
            self.initialized = False
            return False
        self.logger_wifi_module.info("ESP initialization started")
        return self.connect_to_wifi()

    def set_timeout(self, timeout=30):
        # Wait for incoming connection
        tx_data = f"AT+CIPSTO={timeout}"  # Set timeout for 30 seconds
        ret_data = self._send_and_receive_command(tx_data)

        if self.ESP8266_OK_STATUS not in ret_data:
            raise at_set("timeout", tx_data)

    def set_multiple_connections(self, multiple=1):
        tx_data = f"AT+CIPMUX={multiple}"  # Set multiple connections
        ret_data = self._send_and_receive_command(tx_data)

        if self.ESP8266_OK_STATUS not in ret_data:
            raise at_set("multiple connections", tx_data)

    def reset(self):
        # tx_data = "AT+RST"
        tx_data = "AT+RESTORE"
        ret_data = self._send_and_receive_command(tx_data)

        if self.ESP8266_OK_STATUS not in ret_data:
            raise at_set("reset", tx_data)

    def set_server(self, is_server=1):
        tx_data = f"AT+CIPSERVER={is_server}"  # set server
        ret_data = self._send_and_receive_command(tx_data)

        if self.ESP8266_OK_STATUS not in ret_data:
            raise at_set("server", tx_data)

    def set_ssl(self, is_ssl=1):
        tx_data = f"AT+HTTPSSL={is_ssl}"
        ret_data = self._send_and_receive_command(tx_data)

        if self.ESP8266_OK_STATUS not in ret_data:
            raise at_set("server", tx_data)

    def get_at_commands(self):
        tx_data = "AT+CLAC"
        ret_data = self._send_and_receive_command(tx_data, 5)
        if ret_data is not self.ESP8266_ERROR_STATUS:
            return ret_data
        return None

    def get_esp_version(self):
        ret_data = self._send_and_receive_command("AT+GMR", 5)
        if self.ESP8266_ERROR_STATUS not in ret_data:
            return ret_data
        return None

    def get_ip(self):
        ret_data = self._send_and_receive_command("AT+CIFSR")
        if self.ESP8266_OK_STATUS not in ret_data:
            return False
        ret_data = str(ret_data)
        pattern = r'CIFSR:STAIP,"(.*?)"'
        match = ure.search(pattern, ret_data)

        if match:
            staip = match.group(1)
            return staip

        return None

    def create_tcp_connection(self, host, port, is_ssl=False, keepalive=10, attempt=0):
        tx_data = (
            "AT+CIPSTART="
            + '"'
            + ("TCP" if (not is_ssl) else "SSL")
            + '"'
            + ","
            + '"'
            + host
            + '"'
            + ","
            + str(port)
            + ","
            + str(keepalive)
        )
        response = self._send_and_receive_command(tx_data)

        if not response or self.ESP8266_OK_STATUS not in response:
            if "ALREADY CONNECTED" in response:
                self.logger_wifi_module.debug("Already connected")
                return True
            if attempt < 3:
                self.logger_wifi_module.error(
                    f"TCP connection failed:{response}{self.line_separator},retry:{str(attempt + 1) }/3"
                )
                return self.create_tcp_connection(
                    host, port, is_ssl, keepalive, attempt + 1
                )
            raise http_connection_fail(host, port)
        return True

    def close_connection(self, conn_id=None):
        """
        Close a TCP/IP connection.
        """

        tx_data = (
            "AT+CIPCLOSE={}".format(conn_id) if conn_id is not None else "AT+CIPCLOSE"
        )
        ret_data = self._send_and_receive_command(tx_data)

        if "CLOSED" in ret_data:
            self.logger_wifi_module.info("Connection closed successfully.")
        else:
            self.logger_wifi_module.error("Failed to close connection.")

    def send_http_command(self, command, conn_id=None, parse=False):
        tx_data = (
            f"AT+CIPSEND={conn_id},{len(command)}"
            if conn_id is not None
            else f"AT+CIPSEND={len(command)}"
        )

        ret_data = self._send_and_receive_command(tx_data)

        if "> " in ret_data:
            response = self._send_and_receive_command(command)
            if response is None:
                raise http_response_invalid("Empty response")
            (header, body, status_code) = self.parser.parse_http(response, parse)

            if status_code != 200:
                raise http_response_invalid(body)

            return (header, body, status_code)
        else:
            raise http_command_fail(command)
