import utime
import sys
import uio

CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
NOTSET = 0

_level_dict = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
}


class Logger:
    level = NOTSET
    line_separator = "\r" + "\n"

    def __init__(self, name):
        self.name = name
        self.handlers = None

    def _level_str(self, level):
        l = _level_dict.get(level)
        if l is not None:
            return l
        return "LVL%s" % level

    def set_level(self, level):
        self.level = level

    def is_enabled_for(self, level):
        return level >= (self.level or _level)

    def log(self, level, msg, *args):
        if level >= (self.level or _level):
            record = LogRecord(
                self.name, level, None, None, msg, args, None, None, None
            )

            if self.handlers:
                for hdlr in self.handlers:
                    hdlr.emit(record)

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

    def exc(self, e, msg, *args):
        buf = uio.StringIO()
        sys.print_exception(e, uio.TextIOWrapper(buf))
        self.log(ERROR, msg + self.line_separator + buf.getvalue(), *args)

    def exception(self, msg, *args):
        self.log(ERROR, msg, *args)

    def addHandler(self, hdlr):
        if self.handlers is None:
            self.handlers = []
        self.handlers.append(hdlr)

    def get_handlers(self):
        return self.handlers


_level = INFO
_loggers = {}


def getLogger(name=None):
    if name is None:
        name = "root"
    if name in _loggers:
        return _loggers[name]
    if name == "root":
        l = Logger(name)
        sh = StreamHandler()
        sh.formatter = Formatter()
        l.addHandler(sh)
    else:
        l = Logger(name)
    _loggers[name] = l
    return l


def info(msg, *args):
    getLogger(None).info(msg, *args)


def debug(msg, *args):
    getLogger(None).debug(msg, *args)


def basicConfig(level=INFO, filename=None, stream=None, format=None, style="%"):
    global _level, _loggers
    _level = level
    if filename:
        h = FileHandler(filename)
    else:
        h = StreamHandler(stream)
    h.setFormatter(Formatter(format, style=style))
    if root.handlers is not None:
        root.handlers.clear()
    if _loggers != {}:
        _loggers.clear()
    root.addHandler(h)


class Handler:
    def __init__(self):
        self.formatter = Formatter()

    def setFormatter(self, fmt):
        self.formatter = fmt


class StreamHandler(Handler):
    def __init__(self, stream=None):
        self._stream = stream or sys.stderr
        self.terminator = "\n"
        self.formatter = Formatter(
            fmt=" %(asctime)s: "
            + self.terminator
            + "%(name)s (%(levelname)s) : %(message)s"
            + self.terminator
        )

    def emit(self, record):
        self._stream.write(self.formatter.format(record) + self.terminator)
        self.flush()

    def flush(self):
        if self._stream and hasattr(self._stream, "flush"):
            self._stream.flush()


class FileHandler(Handler):
    def __init__(self, filename, mode="a", encoding=None, delay=False):
        super().__init__()

        self.encoding = encoding
        self.mode = mode
        self.delay = delay
        self.terminator = "\n"
        self.filename = filename

        self._f = None
        if not delay:
            self._f = open(self.filename, self.mode)

    def emit(self, record):
        if self._f is None:
            self._f = open(self.filename, self.mode)

        self._f.write(self.formatter.format(record) + self.terminator)

    def close(self):
        if self._f is not None:
            self._f.close()


class Formatter:
    converter = utime.localtime

    def __init__(self, fmt=None, datefmt=None, style="%"):
        self.fmt = fmt or "%(message)s"
        self.datefmt = datefmt

        if style not in ("%", "{"):
            raise ValueError("Style must be one of: %, {")

        self.style = style

    def uses_time(self):
        if self.style == "%":
            return "%(asctime)" in self.fmt
        elif self.style == "{":
            return "{asctime" in self.fmt

    def format(self, record):
        record.message = record.msg % record.args

        if self.uses_time():
            record.asctime = self.format_time(record, self.datefmt)

        if record.exc_info is not None:
            record.exc_text += self.format_exception(record.exc_info)
            record.message += record.terminator + record.exc_text

        if self.style == "%":
            return self.fmt % record.__dict__
        elif self.style == "{":
            return self.fmt.format(**record.__dict__)
        else:
            raise ValueError(
                "Style {0} is not supported by logging.".format(self.style)
            )

    def format_time(self, record, datefmt=None):
        assert datefmt is None
        ct = utime.localtime(record.created)
        return "{0}-{1}-{2} {3}:{4}:{5}".format(*ct)

    def format_exception(self, exc_info):
        raise NotImplementedError()

    def format_stack(self, stack_info):
        raise NotImplementedError()


root = getLogger()


class LogRecord:
    def __init__(
        self, name, level, pathname, lineno, msg, args, exc_info, func=None, sinfo=None
    ):
        ct = utime.time()
        self.created = ct
        self.msecs = (ct - int(ct)) * 1000
        self.name = name
        self.levelno = level
        self.levelname = _level_dict.get(level, None)
        self.pathname = pathname
        self.lineno = lineno
        self.msg = msg
        self.args = args
        self.exc_info = exc_info
        self.func = func
        self.sinfo = sinfo
