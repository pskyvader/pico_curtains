from components.esp.wifi import wifi_module
from components.logger import log_message  # Import the logger
from components.esp.errors import (
    url_invalid,
    url_unsupported,
)
import ure


# Define a log file name
log_file = "espwebclientlog.txt"


class web_client(wifi_module):
    def __init__(self, wifi_ssid, wifi_pass, uart_tx, uart_rx):
        super().__init__(wifi_ssid, wifi_pass, uart_tx, uart_rx)

    def get_url_response(self, url, port=80, user_agent="RPi-Pico"):
        try:
            # Use regular expressions to extract scheme, host, and path
            match = ure.match(r"(https?)://([^/]+)(.*)", url)

            if match:
                scheme, host, path = match.groups()
            else:
                raise url_invalid(url)
            # port = None
            # port = 80 if scheme == "http" else port
            # port = 443 if scheme == "https" else port

            if port is None:
                raise url_unsupported(scheme)

            # get_req = f'AT+HTTPCLIENT=2,0,"{scheme}://{host}{path}","{host}","{path}",2'

            # AT+HTTPCLIENT=1,0,"http://httpbin.org/get","httpbin.org","/get",1
            # response = self._send_and_receive_command(get_req)
            # log_message(response, log_file)

            # if port == 443:
            #     self.set_ssl(), port == 443
            if not self.create_tcp_connection(host, port):
                return (None, None, None)

            # Send an HTTP GET request
            # get_req = "GET {} HTTP/1.1\r\nHost: {}\r\n\r\n".format(path, host)

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
            log_message(f"Failed to get URL response from {url}: {e}", log_file)
            return (None, None, None)
