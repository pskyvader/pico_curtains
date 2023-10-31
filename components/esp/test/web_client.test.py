from components.esp.web_client import web_client
from lib.logging import basicConfig, DEBUG

basicConfig(level=DEBUG)


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
        update_url = "http://192.168.1.231/"
        uart_tx = 4
        uart_rx = 5
        web_client_instance = web_client(wifi_ssid, wifi_pass, uart_tx, uart_rx)

        url = update_url + "lib/logging/__init__.py"
        expected_result = ("mock_header", "mock_body", 200)
        self.assert_equal(
            expected_result, web_client_instance.get_url_response(url, port=3000)
        )

        # Test when an exception is raised
        url = "invalid_url"
        expected_result = (None, None, None)
        self.assert_equal(expected_result, web_client_instance.get_url_response(url))

        # Print the test results
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_failed}")


# Run the tests
test_case = WebClientTestCase()
test_case.run_tests()
