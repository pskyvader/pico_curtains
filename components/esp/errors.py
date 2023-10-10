class url_invalid(Exception):
    def __init__(self, url):
        super().__init__("Invalid URL", str(url))


class url_unsupported(Exception):
    def __init__(self, scheme):
        super().__init__("Unsupported URL scheme", str(scheme))


class http_connection_fail(Exception):
    def __init__(self, host, port):
        super().__init__("Failed to connect to the server", str(host), str(port))


class http_command_fail(Exception):
    def __init__(self, command):
        super().__init__("Failed to send HTTP command: ", str(command))


class http_request_fail(Exception):
    def __init__(self, request):
        super().__init__("Failed to send HTTP request", str(request))


class http_response_invalid(Exception):
    def __init__(self, response):
        super().__init__("Invalid HTTP response", str(response))


class http_response_parse_invalid(Exception):
    def __init__(self, original_exception, response):
        super().__init__(
            "Invalid HTTP parse response: ", str(original_exception), str(response)
        )


class at_empty(Exception):
    def __init__(self, response):
        super().__init__("AT Empty Response", str(response))


class at_unknown(Exception):
    def __init__(self, response):
        super().__init__("AT Unknown error", str(response))


class at_set(Exception):
    def __init__(self, message, request):
        super().__init__(f"AT set {message} error", str(request))
