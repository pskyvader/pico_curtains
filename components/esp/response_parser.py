import ujson
import ure
from components.esp.errors import http_response_parse_invalid
from lib.logging import getLogger, handlers, StreamHandler
import ustruct


class response_parser:
    log_file = "parserlog.txt"

    def __init__(self):
        self.logger_parser = getLogger("parser_module")
        self.logger_parser.addHandler(handlers.RotatingFileHandler(self.log_file))
        self.logger_parser.addHandler(StreamHandler())
        self.line_separator = "\r" + "\n"
        self.line_separator_raw = r"\r" + r"\n"

    def parse_http(self, http_res, parse=False):
        if http_res == None:
            return None, None, None
        try:
            partition_separator = "IP" + "D"
            sub_separator = r"\+" + partition_separator + r",\d+:"
            http_res = http_res.decode("utf-8")

            self.logger_parser.debug("step 1")
            parsed_res = (http_res).partition("+" + partition_separator + ",")

            parsed_res = parsed_res[2]
            self.logger_parser.debug("step 2: %s", str(parsed_res))

            parsed_res = str(parsed_res).partition(self.line_separator * 2)
            self.logger_parser.debug("step 3 len: %s", str(len(parsed_res)))

            self.logger_parser.debug("step 3: %s", parsed_res)
            body_str = ure.sub(sub_separator, "", parsed_res[2])
            self.logger_parser.debug("step 4: %s", parsed_res[0])

            headers_str = ure.sub(sub_separator, "", (parsed_res[0])).partition(":")[2]
            self.logger_parser.debug("step 5")
            status_code = -1
        except Exception as e:
            self.logger_parser.exception("parse error: %s", str(e))
            self.logger_parser.exception("args:%s", str(e.args))
            self.logger_parser.exception("original:%s", http_res)
            self.logger_parser.exception("trace:%s", str(e.__traceback__))
            raise http_response_parse_invalid(e, http_res)

        headers = {}
        for line in headers_str.split(self.line_separator):
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        content_type = headers.get("Content-Type", "").lower()
        self.logger_parser.debug("content type: " + content_type)
        body = body_str
        if parse:
            body = self.content_parser(body_str, content_type)

        for status in str(headers_str.partition(self.line_separator)[0]).split():
            if status.isdigit():
                status_code = int(status)

        return headers, body, status_code

    def content_parser(self, body_str, content_type):
        if "text/html" in content_type:
            try:
                html_parser = HTMLParser()
                return html_parser.parse_html(body_str).to_dict()
            except Exception as e:
                self.logger_parser.exception("HTML parse error: " + str(e))
                return body_str
        elif "application/json" in content_type:
            self.logger_parser.debug("body_str: " + str(body_str))
            try:
                return ujson.loads(body_str)
            except ValueError as e:
                self.logger_parser.critical("JSON parse error: %s", str(e))
                return body_str
        else:
            try:
                return self.parse_file(body_str)
            except Exception as e:
                self.logger_parser.exception("file parse error: %s", str(e))
                return body_str

    def parse_file(self, text):
        self.logger_parser.debug("file content: %s", text)
        return text


class HTMLNode:
    def __init__(self, tag, parent=None):
        self.tag = tag
        self.attributes = {}
        self.children = []
        self.parent = parent
        self.content = None

    def add_child(self, child):
        self.children.append(child)

    def set_attribute(self, name, value):
        self.attributes[name] = value

    def to_dict(self):
        node_dict = {
            "tag": self.tag,
            "attributes": self.attributes,
            "children": [child.to_dict() for child in self.children],
            "content": self.content,
        }
        return node_dict


class HTMLParser:
    def __init__(self):
        self.root = None
        self.current_node = None

    def parse_html(self, html) -> HTMLNode:
        self.root = None
        self.current_node = None

        start = 0
        length = len(html)

        while start < length:
            if html[start] == "<":
                if html[start + 1] == "/":
                    self._process_closing_tag(html, start)
                    start += 1
                else:
                    start = self._process_opening_tag(html, start)
            else:
                start = self._process_text_content(html, start)

        if not self.root:
            self.root = HTMLNode("#none")
        return self.root

    def _process_closing_tag(self, html, start):
        end = html.find(">", start + 1)
        tag = html[start + 2 : end]
        if self.current_node and self.current_node.tag == tag:
            self.current_node = self.current_node.parent

    def _process_opening_tag(self, html, start):
        end = html.find(">", start + 1)
        tag = html[start + 1 : end]
        node = HTMLNode(tag)
        if self.current_node:
            self.current_node.add_child(node)
            node.parent = self.current_node
        else:
            self.root = node
        self.current_node = node
        return end + 1

    def _process_text_content(self, html, start):
        end = html.find("<", start)
        content = html[start:end].strip()
        if content:
            text_node = HTMLNode("#text")
            text_node.content = content
            if self.current_node:
                self.current_node.add_child(text_node)
            else:
                self.root = text_node
        return end
