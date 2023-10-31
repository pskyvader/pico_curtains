from components.updater.updater import updater
from lib.logging import basicConfig, DEBUG

basicConfig(level=DEBUG)


class UpdaterTestCase:
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
        # Create an instance of the updater class with mock values
        updater_instance = updater(
            wifi_ssid="Pabloysofi",
            wifi_pass="jaimitoelperrito",
            update_url="http://192.168.1.231/",
            update_port=3000,
            uart_tx=4,
            uart_rx=5,
        )

        # Test the _download_all_files method
        self.assert_equal(
            True,
            updater_instance._download_all_files(
                ["components/button_control.py", "lib/logging/__init__.py"]
            ),
        )

        # # Test the update_process method
        # self.assert_equal(
        #     False, updater_instance.update_process(["file1.txt", "file2.txt"])
        # )

        # # Test the start_update method
        # self.assert_equal(False, updater_instance.start_update())

        # Print the test results
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_failed}")


# Run the tests
test_case = UpdaterTestCase()
test_case.run_tests()
