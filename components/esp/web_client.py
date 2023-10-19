from components.esp.wifi import wifi_module
from components.esp.errors import (
    url_invalid,
    url_unsupported,
)
import ure
from lib.logging import getLogger, handlers, StreamHandler


class web_client(wifi_module):
    log_file = "espwebclientlog.txt"

    def __init__(self, wifi_ssid, wifi_pass, uart_tx, uart_rx):
        super().__init__(wifi_ssid, wifi_pass, uart_tx, uart_rx)
        self.logger_wifi_client = getLogger("web_client")
        self.logger_wifi_client.addHandler(handlers.RotatingFileHandler(self.log_file))
        self.logger_wifi_client.addHandler(StreamHandler())

    def get_url_response(self, url, port=80, user_agent="RPi-Pico"):
        try:
            match = ure.match(r"(https?)://([^/]+)(.*)", url)

            if match:
                scheme, host, path = match.groups()
            else:
                raise url_invalid(url)

            if port is None:
                raise url_unsupported(scheme)

            if not self.create_tcp_connection(host, port):
                return (None, None, None)

            get_req = (
                "GET "
                + path
                + " HTTP/1.1\r\nHost: "
                + host
                + ":"
                + str(port)
                + "\r\nUser-Agent: "
                + user_agent
                + "\r\n\r\n"
            )

            (header, body, status_code) = self.send_http_command(get_req)
            self.close_connection()
            return (header, body, status_code)

        except Exception as e:
            self.logger_wifi_client.error(f"Failed to get URL response from {url}: {e}")
            return (None, None, None)
