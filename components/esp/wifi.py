import ujson
import ure

from components.esp.espmodule import ESPMODULE
from components.logger import log_message  # Import the logger

from components.esp.errors import (
    http_connection_fail,
    http_command_fail,
    http_response_parse_invalid,
    http_response_invalid,
    at_set,
)

# Define a log file name
log_file = "espwifilog.txt"


class wifi_module(ESPMODULE):
    ESP8266_WIFI_CONNECTED = "WIFI CONNECTED\r\n"
    ESP8266_WIFI_GOT_IP_CONNECTED = "WIFI GOT IP\r\n"
    ESP8266_WIFI_DISCONNECTED = "WIFI DISCONNECT\r\n"
    ESP8266_WIFI_AP_NOT_PRESENT = "WIFI AP NOT FOUND\r\n"
    ESP8266_WIFI_AP_WRONG_PWD = "WIFI AP WRONG PASSWORD\r\n"

    # HTTP_STATUS_OK = "HTTP/1.1 200 OK\r\n"

    def __init__(self, wifi_ssid, wifi_pass, uart_tx, uart_rx):
        self.WIFI_SSID = wifi_ssid
        self.WIFI_PASS = wifi_pass
        super().__init__(uart_tx, uart_rx)
        self.initialized = None  # Use None to indicate not yet initialized

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
            log_message("Pre connect error: " + str(e), log_file)
            return False

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
            ret_data = self._send_and_receive_command(tx_data, delay=5)
        except Exception as e:
            log_message(e, log_file)
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
        log_message("Checking Wi-Fi connection...", log_file)
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
            log_message(e, log_file)

        log_message("Wi-Fi is not connected", log_file)
        return False

    def start(self):
        log_message("Connecting to Wi-Fi...", log_file)
        preconnect = self.pre_connect()
        if not preconnect:
            self.initialized = False
            return False
        log_message("ESP initialization started", log_file)
        self.connect_to_wifi()

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

    def set_server(self, is_server=1):
        tx_data = f"AT+CIPSERVER={is_server}"  # set server
        ret_data = self._send_and_receive_command(tx_data)

        if self.ESP8266_OK_STATUS not in ret_data:
            raise at_set("server", tx_data)

    def set_ssl(self, is_ssl=1):
        # tx_data = f"AT+CIPSSL={is_ssl}"  # Set ssl
        tx_data = f"AT+HTTPSSL={is_ssl}"  # Set ssl
        ret_data = self._send_and_receive_command(tx_data)

        if self.ESP8266_OK_STATUS not in ret_data:
            raise at_set("server", tx_data)

    def get_at_commands(self):
        tx_data = "AT+CLAC"
        ret_data = self._send_and_receive_command(tx_data, 5)
        if ret_data is not None:
            return ret_data.decode()
        return None

    def get_esp_version(self):
        ret_data = self._send_and_receive_command("AT+GMR", 5)
        if ret_data is not None:
            return ret_data.decode()
        return None

    def get_ip(self):
        ret_data = self._send_and_receive_command("AT+CIFSR")
        if self.ESP8266_OK_STATUS not in ret_data:
            return False

        pattern = r'CIFSR:STAIP,"(.*?)"'
        match = ure.search(pattern, ret_data.decode())

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
            if "ALREADY CONNECTED\r\n" in response:
                return True
            if attempt < 3:
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
            log_message("Connection closed successfully.", log_file)
        else:
            log_message("Failed to close connection.", log_file)

    def send_http_command(self, command, conn_id=None):
        tx_data = (
            f"AT+CIPSEND={conn_id},{len(command)}"
            if conn_id is not None
            else f"AT+CIPSEND={len(command)}"
        )

        ret_data = self._send_and_receive_command(tx_data)

        if "> " in ret_data:
            response = self._send_and_receive_command(command, delay=1)
            (header, body, status_code) = self.parse_http(response)

            if status_code != 200:
                raise http_response_invalid(body)

            return (header, body, status_code)
        else:
            raise http_command_fail(command)

    def parse_http(self, http_res):
        """
        This funtion use to parse the HTTP response and return back the HTTP status code

        Return:
            HTTP status code.
        """
        if http_res == None:
            return None, None, None
        try:
            http_res = str(http_res)[1:-1]
            parsed_res = str(http_res).partition("+IPD,")[2]
            parsed_res = parsed_res.split(r"\r\n\r\n")
            body_str = ure.sub(r"\+IPD,\d+:", "", str(parsed_res[1]))
            # .partition( r"\r\n" )[2]
            # body_str = body_str.partition(r"\r\n0")[0]

            headers_str = ure.sub(r"\+IPD,\d+:", "", str(parsed_res[0])).partition(":")[
                2
            ]
            status_code = -1
        except Exception as e:
            raise http_response_parse_invalid(e, http_res)

        # Parse headers into a dictionary
        headers = {}
        for line in headers_str.split(r"\r\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        # Check the content type and parse the body accordingly
        content_type = headers.get("Content-Type", "").lower()
        log_message("content type: " + content_type, log_file)
        body = body_str
        if "text/html" in content_type:
            # If content type is HTML, parse the body as an HTML document
            try:
                body = self.parse_html(body_str)
            except Exception as e:
                log_message("HTML parse error: " + str(e), log_file)
                body = body_str  # Fallback to a string if HTML parsing fails
        elif "application/json" in content_type:
            body_str = body_str.replace(r"\r\n", "")
            log_message("body_str: " + str(body_str), log_file)
            try:
                body = ujson.loads(body_str)
            except ValueError as e:
                log_message("JSON parse error: " + str(e), log_file)
                body = body_str  # Fallback to a string if JSON parsing fails

        for status in str(headers_str.partition(r"\r\n")[0]).split():
            if status.isdigit():
                status_code = int(status)

        return headers, body, status_code

    def parse_html(self, html):
        result = {}
        while "<" in html and ">" in html:
            start = html.index("<") + 1
            end = html.index(">")
            tag = html[start:end]
            html = html[end + 1 :]

            if "<" in html:
                end = html.index("<")
                content = html[:end]
                html = html[end:]
            else:
                content = html
                html = ""

            if tag not in result:
                result[tag] = []
            result[tag].append(content)

        return result
