from components.esp.wifi import wifi_module

from lib.logging import getLogger, handlers, StreamHandler


class web_server(wifi_module):
    log_file = "espwebserver.txt"
    server_line_separator = "\r" + "\n"

    def __init__(self, wifi_ssid, wifi_pass, uart_tx, uart_rx):
        super().__init__(wifi_ssid, wifi_pass, uart_tx, uart_rx)
        self.logger_wifi_server = getLogger("espwebserver")
        self.logger_wifi_server.addHandler(handlers.RotatingFileHandler(self.log_file))
        self.logger_wifi_server.addHandler(StreamHandler())

    def start_web_server(self, port=80):
        """
        Start a simple HTTP server on the ESP8266.
        """
        try:
            # self.set_timeout(30)
            self.set_multiple_connections(1)
            self.set_server(1)
            self.logger_wifi_server.info(f"ESP: Web server started on port {port}.")
            return True
        except Exception as e:
            self.logger_wifi_server.error(
                f"Failed to start web server on port {port}. error: {e}"
            )
            return False

    def handle_web_request(self):
        """
        Handle incoming HTTP requests and perform actions based on the request.
        """
        response = self._receive_command(timeout=10)
        response = response.decode()
        self.logger_wifi_server.debug("Received response: " + response)
        if len(response) <= 0:
            return None, None, None

        if "+IPD," not in response:
            return None, response, None

        conn_id_start = response.index("+IPD,") + 5
        conn_id_end = response.index(",", conn_id_start)
        conn_id = int(response[conn_id_start:conn_id_end])

        request_start = response.find("GET ")
        if request_start == -1:
            request_start = response.find("POST ")
        request_end = -1
        if request_start != -1:
            request_end = response.find(self.server_line_separator * 2, request_start)

        if request_end != -1:
            http_request = response[request_start:request_end]

            headers, request_body = (
                http_request.split(self.server_line_separator * 2, 1)
                if self.server_line_separator * 2 in http_request
                else (http_request, "")
            )

            return headers, request_body, conn_id

        return None, response, None

    def send_web_file(self, conn_id, html_file_path):
        try:
            with open(html_file_path, "r") as html_file:
                html_content = html_file.read()
        except OSError as e:
            self.logger_wifi_server.error(f"Failed to read HTML file: {e}")
            self.send_404_response(conn_id)
            return False

        http_header = (
            "HTTP/1.1 200 OK"
            + self.server_line_separator
            + "Content-Type: text/html"
            + self.server_line_separator
            + "Transfer-Encoding: chunked"
            + self.server_line_separator * 2
        )

        header_response = self._send_response(conn_id, http_header)
        if header_response is False:
            return False

        max_chunk_size = self.UART_RX_BUFFER_LENGTH - 16
        for i in range(0, len(html_content), max_chunk_size):
            chunk = html_content[i : i + max_chunk_size]

            chunk_data = (
                f"{len(chunk):X}{self.server_line_separator}{chunk}{self.server_line_separator*2}"
            )
            chunk_response = self._send_response(conn_id, chunk_data)
            if chunk_response is False:
                return False

        final_response = self._send_response(conn_id, "0" + self.server_line_separator)
        if final_response is False:
            self.logger_wifi_server.error("Failed to send final chunk. ")
            return False

        self.logger_wifi_server.info("Final chunk sent.")

        self.close_connection(conn_id)

    def send_ok_response(self, conn_id):
        html_response = (
            "HTTP/1.1 200 OK"
            + self.server_line_separator
            + "Content-Length: 2"
            + self.server_line_separator * 2
            + "OK"
        )
        self._send_response(conn_id, html_response)

    def send_404_response(self, conn_id):
        html_response = (
            "HTTP/1.1 404 Not Found"
            + self.server_line_separator
            + "Content-Length: 9"
            + self.server_line_separator * 2
            + "Not Found"
        )
        self._send_response(conn_id, html_response)

    def _send_response(self, conn_id, response):
        """
        Send an HTTP response to the client.
        """
        tx_data = f"AT+CIPSEND={conn_id},{len(response)}{self.server_line_separator}"
        ret_data = self._send_and_receive_command(tx_data)

        if "> " in str(ret_data):
            return self._send_and_receive_command(response)
        else:
            self.logger_wifi_server.critical(
                "Failed to send HTTP response: " + str(ret_data)
            )
            return False
