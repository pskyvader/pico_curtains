from components.esp.wifi import wifi_module
from lib.logging import basicConfig, INFO
from components.connection_manager import connect_process

basicConfig(level=INFO)


class WebClientTestCase:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0

    def assert_equal(self, expected, actual):
        if expected == actual:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            print(f"Test failed: expected {expected}, but got {actual}")

    def run_tests(self):
        # Create an instance of the web_client class with mock values

        wifi_ssid = "Pabloysofi"
        wifi_pass = "jaimitoelperrito"
        uart_tx = 4
        uart_rx = 5
        baudrate = int(115200)

        wifi_instance = wifi_module(
            wifi_ssid, wifi_pass, uart_tx, uart_rx, baudrate=baudrate
        )
        # print(wifi_instance._send_and_receive_command("AT"))
        # wifi_instance.reset()
        # wifi_instance.get_esp_version()
        connect_process(wifi_instance)
        self.assert_equal(True, wifi_instance.is_initialized())
        if not wifi_instance.is_initialized():
            print("No connection, update aborted.")
            return False

        path = "/components/esp/response_parser.py"
        # path = "/"
        host = "192.168.1.231"
        port = 3000
        user_agent = "ESP8266/1.0"

        expected_result = ("mock_header", "mock_body", 200)

        tcp_result = wifi_instance.create_tcp_connection(
            host="192.168.1.231", port=3000
        )
        self.assert_equal(True, tcp_result)

        get_req = (
            "GET "
            + path
            + " HTTP/1.1"
            + wifi_module.line_separator
            + "Host: "
            + host
            + ":"
            + str(port)
            + wifi_module.line_separator
            + "User-Agent: "
            + user_agent
            + wifi_module.line_separator * 2
        )

        (header, body, status_code) = wifi_instance.send_http_command(get_req)
        wifi_instance.close_connection()

        self.assert_equal(expected_result, (header, body, status_code))

        try:
            with open(path, "wb") as file_object:
                print(f"file {path} open")
                file_content = body
                file_object.write(file_content)
        except OSError as e:
            print(f"Failed to write file{path}:" + str(e))
            return False

        # Print the test results
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_failed}")


# Run the tests
test_case = WebClientTestCase()
test_case.run_tests()
