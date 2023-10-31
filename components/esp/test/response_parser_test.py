from components.esp.response_parser import response_parser
from lib.logging import basicConfig, INFO
import time

basicConfig(level=INFO)


class ResponseParserTestCase:
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
        start_time = time.time()
        parser_instance = response_parser()

        with open("/components/esp/test/test_parser_source.py", "r") as f:
            original_text = f.read()
        with open("/components/esp/response_parser.py", "r") as f:
            expected_result = f.read()
        test_result = parser_instance.parse_file(original_text)

        with open("/components/esp/test/test_parser_result.py", "w") as f:
            f.write(test_result)

        self.assert_equal(expected_result, test_result)

        # Print the test results
        print(f"Tests passed: {self.tests_passed}")
        print(f"Tests failed: {self.tests_failed}")
        print(f"Total time: {time.time()-start_time}")


# Run the tests
test_case = ResponseParserTestCase()
test_case.run_tests()
