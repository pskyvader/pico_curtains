from components.esp.web_client import web_client
from components.logger import log_message
from machine import Timer
import time
import sys
import ujson
import os


class updater:
    version_file = "version.json"
    log_file = "updater_log.txt"
    continue_program = True
    timeout_seconds = 30
    start_time = time.time()

    def __init__(
        self, wifi_ssid, wifi_pass, update_url, update_port=80, uart_tx=4, uart_rx=5
    ) -> None:
        self.update_url = update_url
        self.update_port = update_port
        self.esp_process = web_client(
            wifi_ssid=wifi_ssid, wifi_pass=wifi_pass, uart_tx=uart_tx, uart_rx=uart_rx
        )

    def stop_update(self):
        self.continue_program = False

    def waiting_message(self, times=0):
        if (
            self.continue_program
            and self.esp_process.is_initialized() is None
            and time.time() - self.start_time < self.timeout_seconds
        ):
            sys.stdout.write("Waiting for ESP initialization... [" + "=" * times)
            sys.stdout.write("]\r")
            timer = Timer()
            timer.init(
                period=500,
                mode=Timer.ONE_SHOT,
                callback=lambda t: self.waiting_message(times + 1),
            )

    def connect_process(self, attempt=0):
        self.esp_process.initialized = None
        if self.esp_process.is_wifi_connected():
            log_message("ESP already connected", self.log_file)
            self.esp_process.initialized = True
            ip = self.esp_process.get_ip()
            log_message("IP:" + ip, self.log_file)
            return

        self.waiting_message()
        if attempt == 0:
            self.esp_process.start()
        else:
            self.esp_process.connect_to_wifi()
        if not self.esp_process.is_initialized():
            log_message("ESP initialization failed", self.log_file)
            if self.continue_program and attempt < 3:
                log_message("Retry", self.log_file)
                self.connect_process(attempt + 1)
            else:
                return False
        else:
            log_message("ESP initialization succeeded", self.log_file)
            ip = self.esp_process.get_ip()
            log_message("IP:" + ip, self.log_file)

    def get_local_version(self, file_location=None):
        if file_location is None:
            file_location = self.version_file
        try:
            with open(file_location, "r") as file:
                json_data = file.read()

                parsed_json = ujson.loads(json_data)
                if parsed_json and parsed_json["version"]:
                    log_message(
                        "Local Version: " + str(parsed_json["version"]), self.log_file
                    )
                    return parsed_json["version"]
                return None

        except OSError as e:
            print("Error reading JSON file:", e)
            return None

    def get_version(self, files_list):
        url = self.update_url
        port = self.update_port

        matches = [match for match in files_list if self.version_file in match]
        if len(matches) > 0:
            (header, body, status_code) = self.esp_process.get_url_response(
                url + self.version_file, port
            )
            if body == None or not body["version"]:
                log_message("No version body found", self.log_file)
                return False

            log_message("Remote Version: " + str(body["version"]), self.log_file)
            local_version = self.get_local_version()
            if local_version is not None and body["version"] > local_version:
                return True

        return False

    def create_backup(self, backup_directory="/backup"):
        try:
            # Create an empty backup directory or clear existing files
            if os.path.exists(backup_directory):
                self._remove_directory(backup_directory)
            os.mkdir(backup_directory)

            # Copy every file, subfolder, and files in those subfolders from the root "/" to the backup directory
            for root, dirs, files in os.ilistdir("/"):
                for entry in dirs + files:
                    # Get the absolute path of the file or subdirectory
                    entry_path = os.path.join(root, entry)

                    # Get the corresponding path within the backup directory
                    backup_path = os.path.join(backup_directory, entry_path[1:])

                    # Create the necessary directories in the backup directory if they don't exist
                    self._makedirs(os.path.dirname(backup_path))

                    # Copy the file or subdirectory to the backup directory
                    if entry[0] == 0x4000:  # Directory flag
                        self._mkdir(backup_path)
                    else:
                        self._copy_file(entry_path, backup_path)

            # If everything goes well, return True
            log_message("Backup created successfully", self.log_file)
            return True
        except Exception as e:
            log_message("Failed to create backup: {}".format(e), self.log_file)
            return False

    def _remove_directory(self, directory):
        for root, dirs, files in os.ilistdir(directory):
            for entry in dirs + files:
                entry_path = os.path.join(root, entry)
                if entry[0] == 0x4000:  # Directory flag
                    self._remove_directory(entry_path)
                else:
                    os.remove(entry_path)
        os.rmdir(directory)

    def _makedirs(self, directory):
        if not os.path.exists(directory):
            parent = os.path.dirname(directory)
            if parent and not os.path.exists(parent):
                self._makedirs(parent)
            os.mkdir(directory)

    def _mkdir(self, directory):
        if not os.path.exists(directory):
            os.mkdir(directory)

    def _copy_file(self, src, dst):
        with open(src, "rb") as src_file, open(dst, "wb") as dst_file:
            while True:
                chunk = src_file.read(4096)
                if not chunk:
                    break
                dst_file.write(chunk)

    def update_process(self, files_list):
        try:
            for file_url in files_list:
                # Download the file from the specified URL
                (header, body, status_code) = self.esp_process.get_url_response(
                    file_url
                )

                # Check if the download was successful (status code 200)
                if status_code != 200:
                    log_message(f"Failed to download file: {file_url}", self.log_file)
                    return False

                # Extract the route (folder/file path) from the URL
                route = file_url.split("/", 3)[-1]

                # Create any necessary subdirectories
                folder_path = os.path.dirname(route)
                if folder_path:
                    os.makedirs(folder_path, exist_ok=True)

                # Write the downloaded file contents to the appropriate file
                with open(route, "wb") as f:
                    f.write(body)

            # If everything goes well, return True
            log_message("Update process completed successfully", self.log_file)
            return True
        except Exception as e:
            log_message(f"Failed to update process: {e}", self.log_file)
            return False

    def rollback(self, backup_directory="/backup"):
        try:
            # Check if the backup directory exists
            if not os.path.exists(backup_directory):
                log_message("Backup directory not found", self.log_file)
                return False

            # Remove all existing files and directories
            for root, dirs, files in os.walk("/"):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))

            # Restore files from the backup directory
            for root, dirs, files in os.walk(backup_directory):
                for file in files:
                    # Get the absolute path of the file in the backup directory
                    backup_file = os.path.join(root, file)

                    # Get the corresponding path within the root directory
                    restore_file = os.path.join(
                        "/", os.path.relpath(backup_file, backup_directory)
                    )

                    # Create the necessary directories in the root directory if they don't exist
                    self._makedirs(os.path.dirname(restore_file))

                    # Copy the file from the backup directory to the root directory
                    self._copy_file(backup_file, restore_file)

            # If everything goes well, return True
            log_message("Rollback successful", self.log_file)
            return True
        except Exception as e:
            log_message(f"Failed to rollback: {e}", self.log_file)
            return False

    def start_update(self):
        self.connect_process()

        if not self.esp_process.is_initialized():
            log_message("No connection, update aborted.", self.log_file)
            return False

        url = self.update_url
        port = self.update_port
        (header, body, status_code) = self.esp_process.get_url_response(url, port)
        if body == None:
            log_message("No body found", self.log_file)
            return False
        if not self.get_version(body):
            log_message(
                "No update found. Already updated to the last version",
                self.log_file,
            )
            return False
        log_message("Update found. Updating new version...", self.log_file)
        if not self.create_backup():
            log_message("Backup failed, aborting", self.log_file)
            return False

        if not self.update_process(body):
            log_message("Update fail, rolling back", self.log_file)
            if self.rollback():
                log_message("Rolled back. booting old version...", self.log_file)
                return False
            log_message("Rolled back failed, RUUUUN B1TCH, RUUUUN!!!!", self.log_file)
            return False
        log_message("Update succeded. booting new version...", self.log_file)
        return True
