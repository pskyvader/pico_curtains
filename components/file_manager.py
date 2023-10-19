import os
from lib.logging import getLogger, handlers, StreamHandler


class FileManager:
    """
    A class to update your MicroController with the latest version from a GitHub tagged release,
    optimized for low power usage.
    """

    main_dir = ""
    new_version_dir = ""
    backup_dir = ""
    log_file = "file_manager.txt"
    supports_rename = False

    def __init__(self, main_dir, new_version_dir, backup_dir):
        self.main_dir = main_dir
        self.new_version_dir = new_version_dir
        self.backup_dir = backup_dir

        self.logger_file_manager = getLogger("connection_manager")
        self.logger_file_manager.addHandler(handlers.RotatingFileHandler(self.log_file))
        self.logger_file_manager.addHandler(StreamHandler())
        if self.supports_rename:
            self.logger_file_manager.debug("rename supported")
            self.supports_rename = True

    def _rmtree(self, directory, preserve=[]):
        for entry in os.ilistdir(directory):
            is_dir = entry[1] == 0x4000
            path = directory + "/" + entry[0]
            if directory == "":
                path = entry[0]
            if is_dir:
                self._rmtree(path, preserve)
            else:
                if path.split("/")[0] not in preserve:
                    self.logger_file_manager.debug(f"remove file: {path}")
                    os.remove(path)
        if directory.split("/")[0] not in preserve:
            self.logger_file_manager.debug(f"remove directory: {directory}")
            os.rmdir(directory)

    def _os_supports_rename(self) -> bool:
        self._mk_dirs("otaUpdater/osRenameTest")
        os.rename("otaUpdater", "otaUpdated")
        result = len(os.listdir("otaUpdated")) > 0
        self._rmtree("otaUpdated")
        return result

    def _copy_directory(self, from_path, to_path, exclude=[]):
        self.logger_file_manager.debug(f"copy: {from_path} -> {to_path}")
        # path = to_path.split("/")[0]
        # if path == self.backup_dir or path == self.new_version_dir:
        #     return
        if not self._exists_dir(to_path):
            self._mk_dirs(to_path)

        for entry in os.ilistdir(from_path):
            is_dir = entry[1] == 0x4000
            path = from_path + "/" + entry[0]
            if from_path == "":
                path = entry[0]
            if is_dir:
                if path.split("/")[0] not in exclude:
                    self._copy_directory(path, to_path + "/" + entry[0])
            else:
                if path not in exclude:
                    self._copy_file(path, to_path + "/" + entry[0])

    def _copy_file(self, from_path, to_path):
        self.logger_file_manager.debug(f"copy file: {from_path} -> {to_path}")
        try:
            with open(
                from_path, "rb"
            ) as from_file:  # Use binary mode to handle non-text files
                with open(to_path, "wb") as to_file:
                    CHUNK_SIZE = 4096  # bytes (you can adjust this)
                    data = from_file.read(CHUNK_SIZE)
                    while data:
                        to_file.write(data)
                        data = from_file.read(CHUNK_SIZE)

        except FileNotFoundError:
            self.logger_file_manager.exception(f"File not found: {from_path}")
        except PermissionError:
            self.logger_file_manager.exception(f"Permission denied: {from_path} or {to_path}")
        except Exception as e:
            self.logger_file_manager.exception(f"An error occurred: {e}")

    def _exists_dir(self, path) -> bool:
        try:
            os.listdir(path)
            return True
        except Exception:
            return False

    def _mk_dirs(self, path: str):
        paths = path.split("/")

        path_to_create = ""
        for x in paths:
            self.logger_file_manager.debug(f"create path at {path_to_create + x}")
            self.mkdir(path_to_create + x)
            path_to_create = path_to_create + x + "/"

    # different micropython versions act differently when directory already exists
    def mkdir(self, path: str):
        try:
            os.mkdir(path)
        except OSError as exc:
            if exc.args[0] == 17:
                pass
