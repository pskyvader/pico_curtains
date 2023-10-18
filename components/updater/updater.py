from components.esp.web_client import web_client
from components.connection_manager import connect_process
from components.updater.version_manager import get_version
from components.updater.backup_manager import BackupManager
import uos

from lib.logging import getLogger, handlers


class updater:
    version_file = "version.json"
    log_file = "updater_log.txt"

    def __init__(
        self, wifi_ssid, wifi_pass, update_url, update_port=80, uart_tx=4, uart_rx=5
    ) -> None:
        self.update_url = update_url
        self.update_port = update_port
        self.esp_process = web_client(
            wifi_ssid=wifi_ssid, wifi_pass=wifi_pass, uart_tx=uart_tx, uart_rx=uart_rx
        )
        self.backup_manager = BackupManager(
            main_dir="", backup_dir="backup", new_version_dir="new"
        )
        self.logger = getLogger("updater")
        self.logger.addHandler(handlers.RotatingFileHandler(self.log_file))

    def _download_all_files(self, files_list):
        for file_url in files_list:
            file_path = (
                self.backup_manager.new_version_dir + "/" + file_url.split("/", 3)[-1]
            )

            (header, body, status_code) = self.esp_process.get_url_response(file_url)
            if status_code != 200:
                self.logger.error(f"Failed to download file: {file_url}")
                return False
            try:
                with open(file_path, "w") as file_object:
                    file_object.write(str(body) + "\n")
            except OSError as e:
                self.logger.error(f"Failed to write file {file_url}:" + str(e))
                return False
        return True

    def update_process(self, files_list):
        self.logger.info("Update found. Updating new version...")
        if not self.backup_manager.create_backup():
            self.logger.error("Backup failed, aborting")
            return False

        try:
            if not self._download_all_files(files_list):
                self.logger.error("Failed to download update, rolling back")
                if self.backup_manager.restore_backup():
                    self.logger.info("Rolled back. booting old version...")
                    return False
                self.logger.critical("Rolled back failed, RUUUUN B1TCH, RUUUUN!!!!")
                return False
            self.backup_manager.delete_old_version()
            self.backup_manager.install_new_version()
            # If everything goes well, return True
            self.logger.info("Update process completed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update process: {e}")
            return False

    def start_update(self):
        connect_process(
            self.esp_process,
            self.log_file,
        )

        if not self.esp_process.is_initialized():
            self.logger.error("No connection, update aborted.")
            return False

        url = self.update_url
        port = self.update_port
        (header, body, status_code) = self.esp_process.get_url_response(url, port)
        if body == None:
            self.logger.error("No body found")
            return False
        if not get_version(
            self.esp_process,
            self.update_url,
            self.update_port,
            self.version_file,
            self.log_file,
            body,
        ):
            self.logger.info(
                "No update found. Already updated to the last version",
                self.log_file,
            )
            return False
        if not self.update_process(body):
            return False

        self.logger.info("Update succeded. booting new version...")
        return True
